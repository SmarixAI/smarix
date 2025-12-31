"""
Ultra-Fast Gmail Collector (Whitelist Mode)
-------------------------------------------

Key Optimizations:
1. Batch metadata fetching (50 messages per API call)
2. Sequential processing (most reliable, no SSL errors)
3. Conservative rate limiting
4. Exponential backoff with jitter

PHASE A (fast):
    - List message refs in pages (500 at a time)
    - Batch fetch metadata (50 at a time)
    - Filter by sender domain
    - Stop when max_whitelisted reached

PHASE B (sequential/parallel):
    - Default: Sequential processing (reliable, ~1-2 messages/sec)
    - Optional: Parallel with thread-local services (faster but may have SSL errors)
    - Process in chunks of 100

Performance:
    - Phase A: ~5-10 minutes for 20K emails
    - Phase B (sequential): ~1-2 hours for 5K messages
    - Phase B (parallel): ~20-40 minutes for 5K messages (if no SSL errors)

Storage: ../../data/DataCollectionFromGmail/
"""

import os
import base64
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore
import random
import socket

from googleapiclient.errors import HttpError

from .gmail_client import build_gmail_service
from .message_processor import sanitize_message_record


# -----------------------------------------------------------
#              CONSTANTS & WHITELIST CONFIG
# -----------------------------------------------------------

SKIP_LABELS = {
    "CATEGORY_PROMOTIONS",
    "CATEGORY_SOCIAL",
    "CATEGORY_FORUMS",
    "CATEGORY_UPDATES",
    "CATEGORY_SPAM",
    "SPAM",
    "TRASH",
}

METADATA_HEADERS = ["From", "Subject", "Date", "To", "Cc"]

WHITELIST_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "sc.com",
    "icici.com",
    "amdocs.com",
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "atlassian.com",
    "stackshare.io",
    "stackoverflow.com",
    "sourceforge.net",
    "apache.org",
    "npmjs.com",
    "python.org",
}

class GmailCollector:
    def __init__(self, service=None, user_id="me"):
        self.service = service or build_gmail_service()
        self.user_id = user_id

        self.attachments_root = Path("../../data/DataCollectionFromGmail/attachments")
        self.attachments_root.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.rate_limit_lock = Lock()
        self.last_request_time = 0
        self.min_request_interval = 0.15  # 150ms between requests (reduced from 100ms)

        # Thread-local storage for service instances
        import threading
        self._thread_local = threading.local()

    def _get_thread_service(self):
        """Get or create a Gmail service instance for the current thread."""
        if not hasattr(self._thread_local, 'service'):
            self._thread_local.service = build_gmail_service()
        return self._thread_local.service

    def _execute_with_retries(self, request_maker, retries=7, action_desc="operation", use_thread_service=False):
        """Run Gmail API call with exponential backoff and rate limiting."""
        for attempt in range(1, retries + 1):
            # Rate limiting: ensure minimum time between requests
            with self.rate_limit_lock:
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                if time_since_last < self.min_request_interval:
                    time.sleep(self.min_request_interval - time_since_last)
                self.last_request_time = time.time()

            try:
                req = request_maker()
                return req.execute()
            except HttpError as e:
                if e.resp.status == 429:  # Rate limit exceeded
                    # Exponential backoff with jitter
                    base_delay = min(2 ** attempt, 64)  # Cap at 64 seconds
                    jitter = random.uniform(0, 0.3 * base_delay)
                    delay = base_delay + jitter

                    print(f"[gmail_collector] 429 Rate limit hit (attempt {attempt}/{retries})")
                    print(f"[gmail_collector] Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)

                    if attempt == retries:
                        raise
                elif e.resp.status in [500, 503]:  # Server errors
                    delay = min(2 ** attempt, 32)
                    print(f"[gmail_collector] Server error {e.resp.status} (attempt {attempt}/{retries})")
                    time.sleep(delay)
                    if attempt == retries:
                        raise
                else:
                    raise
            except (socket.error, OSError) as e:
                # SSL/TLS connection errors
                error_str = str(e).lower()
                if 'ssl' in error_str or 'connection' in error_str or 'socket' in error_str:
                    delay = min(2 ** (attempt + 1), 16)  # Longer delays for SSL errors
                    print(f"[gmail_collector] SSL/Connection error (attempt {attempt}/{retries}): {e}")
                    print(f"[gmail_collector] Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                    if attempt == retries:
                        raise
                else:
                    raise
            except Exception as e:
                if attempt == retries:
                    raise
                error_str = str(e).lower()
                if 'ssl' in error_str or 'connection' in error_str:
                    delay = min(2 ** (attempt + 1), 16)
                    print(f"[gmail_collector] {action_desc} SSL error (attempt {attempt}): {e}")
                else:
                    delay = min(2 ** attempt, 16)
                    print(f"[gmail_collector] {action_desc} failed (attempt {attempt}): {e}")
                time.sleep(delay)

    def _extract_sender_domain(self, headers: List[Dict]) -> Optional[str]:
        """Extract sender domain from headers."""
        for h in headers:
            if h.get("name", "").lower() == "from":
                val = h.get("value", "")
                if "@" in val:
                    domain = val.split("@")[-1].strip().lower()
                    domain = domain.replace(">", "").replace("<", "")
                    return domain
        return None

    def _is_domain_whitelisted(self, domain: Optional[str]) -> bool:
        if not domain:
            return False
        return domain.lower() in WHITELIST_DOMAINS

    def _batch_get_metadata(self, message_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetch metadata for multiple messages using batch request.
        Gmail API supports up to 100 requests per batch.
        Includes retry logic for rate limiting.
        """
        from googleapiclient.http import BatchHttpRequest

        results = []
        errors = []

        def callback(request_id, response, exception):
            if exception:
                errors.append((request_id, exception))
            elif response:
                results.append(response)

        # Try with retries
        for attempt in range(1, 6):
            try:
                batch = self.service.new_batch_http_request(callback=callback)

                for msg_id in message_ids:
                    batch.add(
                        self.service.users().messages().get(
                            userId=self.user_id,
                            id=msg_id,
                            format="metadata",
                            metadataHeaders=METADATA_HEADERS,
                        )
                    )

                # Add small delay before batch execution
                time.sleep(0.2)
                batch.execute()
                break  # Success

            except HttpError as e:
                if e.resp.status == 429 and attempt < 5:
                    delay = min(2 ** attempt, 32) + random.uniform(0, 2)
                    print(f"[gmail_collector] Batch 429 error (attempt {attempt}/5), waiting {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"[gmail_collector] Batch execution failed: {e}")
                    break
            except Exception as e:
                print(f"[gmail_collector] Batch execution failed: {e}")
                break

        if errors and len(errors) > len(message_ids) * 0.5:
            print(f"[gmail_collector] Warning: {len(errors)} errors in batch of {len(message_ids)}")

        return results

    def _collect_attachment_parts(self, part: Dict[str, Any], collector: List[Dict[str, Any]]):
        """Recursively extract attachment parts from MIME tree."""
        filename = part.get("filename")
        body = part.get("body", {})
        att_id = body.get("attachmentId")

        if filename and att_id:
            collector.append({
                "filename": filename,
                "attachmentId": att_id,
                "mimeType": part.get("mimeType"),
            })

        for sub in part.get("parts", []) or []:
            self._collect_attachment_parts(sub, collector)

    def _download_attachment(self, message_id: str, part_meta: Dict[str, Any], use_thread_service=False):
        """Download attachment bytes and save to disk."""
        service = self._get_thread_service() if use_thread_service else self.service

        try:
            def make_call():
                return service.users().messages().attachments().get(
                    userId=self.user_id,
                    messageId=message_id,
                    id=part_meta["attachmentId"],
                )
            data = self._execute_with_retries(make_call, action_desc="download attachment", use_thread_service=use_thread_service)
        except Exception as e:
            print(f"[gmail_collector] attachment download failed for {message_id}: {e}")
            return None

        data_b64 = data.get("data")
        if not data_b64:
            return None

        try:
            file_bytes = base64.urlsafe_b64decode(data_b64.encode())
        except Exception:
            try:
                file_bytes = base64.b64decode(data_b64.encode())
            except Exception:
                return None

        msg_dir = self.attachments_root / message_id
        msg_dir.mkdir(parents=True, exist_ok=True)
        save_path = msg_dir / part_meta["filename"]

        try:
            with open(save_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            print(f"[gmail_collector] write attachment failed: {e}")
            return None

        return {
            "filename": part_meta["filename"],
            "mimeType": part_meta.get("mimeType"),
            "saved_path": str(save_path),
        }

    def collect_all_messages(
        self,
        show_progress=True,
        max_whitelisted=None,  # None = no limit, process ALL whitelisted
        page_size=500,  # Increased from 100
        batch_size=50,  # Reduced from 100 to avoid rate limits
        max_workers=1,  # Set to 1 for sequential (most reliable)
        phase_b_chunk_size=100,  # Smaller chunks to reduce connection load
        batch_delay=0.5,  # Delay between batches (seconds)
        use_threading=False,  # Default to sequential for stability
        request_delay=0.2,  # Delay between individual requests in sequential mode
    ):

        if show_progress:
            print("\n[gmail_collector] PHASE A — Fast Metadata Scan (Batched)")
            if max_whitelisted:
                print(f"[gmail_collector] Target: {max_whitelisted} whitelisted messages")
            else:
                print(f"[gmail_collector] Target: ALL whitelisted messages")

        whitelisted_ids: List[str] = []
        next_token = None
        page = 0

        query = "in:inbox -category:(promotions OR social OR updates OR forums)"

        while max_whitelisted is None or len(whitelisted_ids) < max_whitelisted:
            page += 1

            # List message IDs
            try:
                def make_list_call():
                    return self.service.users().messages().list(
                        userId=self.user_id,
                        maxResults=page_size,
                        pageToken=next_token,
                        q=query,
                    )
                resp = self._execute_with_retries(make_list_call, action_desc="list messages")
            except Exception as e:
                print(f"[gmail_collector] Error listing messages: {e}")
                break

            refs = resp.get("messages", []) or []
            if show_progress:
                print(f"[gmail_collector] Page {page} — fetched {len(refs)} refs")

            if not refs:
                break

            # Collect message IDs
            msg_ids = [ref["id"] for ref in refs if ref.get("id")]

            # Batch fetch metadata in chunks of batch_size
            for i in range(0, len(msg_ids), batch_size):
                chunk = msg_ids[i:i + batch_size]

                if show_progress:
                    print(f"[gmail_collector] Batch fetching metadata for {len(chunk)} messages...")

                metadata_list = self._batch_get_metadata(chunk)

                # Delay between batches to avoid rate limits
                if i + batch_size < len(msg_ids):
                    time.sleep(batch_delay)

                # Filter by domain
                for meta in metadata_list:
                    if max_whitelisted and len(whitelisted_ids) >= max_whitelisted:
                        break

                    msg_id = meta.get("id")
                    if not msg_id:
                        continue

                    # Check labels
                    labels = meta.get("labelIds", [])
                    if any(lbl in SKIP_LABELS for lbl in labels):
                        continue

                    # Check domain
                    headers = meta.get("payload", {}).get("headers", []) or []
                    domain = self._extract_sender_domain(headers)

                    if self._is_domain_whitelisted(domain):
                        whitelisted_ids.append(msg_id)

                if show_progress:
                    if max_whitelisted:
                        print(f"[gmail_collector] Whitelisted: {len(whitelisted_ids)}/{max_whitelisted}")
                    else:
                        print(f"[gmail_collector] Whitelisted: {len(whitelisted_ids)}")

                if max_whitelisted and len(whitelisted_ids) >= max_whitelisted:
                    break

            next_token = resp.get("nextPageToken")
            if not next_token or (max_whitelisted and len(whitelisted_ids) >= max_whitelisted):
                break

        if show_progress:
            print(f"[gmail_collector] PHASE A complete — {len(whitelisted_ids)} whitelisted messages")

        if not whitelisted_ids:
            return {"source": "gmail", "total_messages": 0, "messages": []}

        # ========== PHASE B: Full Fetch + Attachments ==========
        if show_progress:
            mode = "Parallel" if use_threading else "Sequential"
            print(f"\n[gmail_collector] PHASE B — Fetching {len(whitelisted_ids)} full messages ({mode}, Chunked)")
            if use_threading:
                print(f"[gmail_collector] Using {max_workers} workers, chunk size {phase_b_chunk_size}")
            else:
                print(f"[gmail_collector] Sequential mode (safe), chunk size {phase_b_chunk_size}")

        results: List[Dict[str, Any]] = []

        def worker(msg_id: str):
            """Worker function - uses thread-local service instance."""
            try:
                # Get thread-local service instance (thread-safe)
                thread_service = self._get_thread_service()

                # Fetch full message
                def make_full_call():
                    return thread_service.users().messages().get(
                        userId=self.user_id,
                        id=msg_id,
                        format="full",
                    )
                msg_full = self._execute_with_retries(make_full_call, action_desc="full message", use_thread_service=True)

                # Sanitize
                sanitized = sanitize_message_record(msg_full, keep_snippet=True)

                # Attachments
                payload = msg_full.get("payload", {}) or {}
                parts = []
                self._collect_attachment_parts(payload, parts)

                attachments = []
                for p in parts:
                    att = self._download_attachment(msg_id, p, use_thread_service=True)
                    if att:
                        attachments.append(att)

                sanitized["attachments"] = attachments
                return sanitized
            except Exception as e:
                print(f"[gmail_collector] Worker error for {msg_id}: {e}")
                return None

        # Process in smaller chunks to avoid SSL connection exhaustion
        total_processed = 0

        for chunk_start in range(0, len(whitelisted_ids), phase_b_chunk_size):
            chunk_end = min(chunk_start + phase_b_chunk_size, len(whitelisted_ids))
            chunk_ids = whitelisted_ids[chunk_start:chunk_end]

            chunk_num = chunk_start // phase_b_chunk_size + 1
            total_chunks = (len(whitelisted_ids) + phase_b_chunk_size - 1) // phase_b_chunk_size

            if show_progress:
                print(f"\n[gmail_collector] Processing chunk {chunk_num}/{total_chunks}: messages {chunk_start+1}-{chunk_end}")

            chunk_completed = 0
            chunk_success = 0

            if use_threading:
                # Parallel processing with thread pool
                with ThreadPoolExecutor(max_workers=max_workers) as exe:
                    fut_map = {exe.submit(worker, mid): mid for mid in chunk_ids}

                    for fut in as_completed(fut_map):
                        res = fut.result()
                        if res:
                            results.append(res)
                            chunk_success += 1

                        chunk_completed += 1
                        total_processed += 1

                        if show_progress and chunk_completed % 25 == 0:
                            print(f"[gmail_collector] Chunk {chunk_num}: {chunk_completed}/{len(chunk_ids)} | Success: {chunk_success} | Total: {total_processed}/{len(whitelisted_ids)}")
            else:
                # Sequential processing (safer, but slower)
                for idx, mid in enumerate(chunk_ids, 1):
                    res = worker(mid)
                    if res:
                        results.append(res)
                        chunk_success += 1

                    chunk_completed += 1
                    total_processed += 1

                    if show_progress and chunk_completed % 10 == 0:
                        print(f"[gmail_collector] Chunk {chunk_num}: {chunk_completed}/{len(chunk_ids)} | Success: {chunk_success} | Total: {total_processed}/{len(whitelisted_ids)}")

                    # Small delay between requests in sequential mode
                    if idx < len(chunk_ids):
                        time.sleep(request_delay)

            if show_progress:
                print(f"[gmail_collector] Chunk {chunk_num} complete: {chunk_success}/{len(chunk_ids)} successful")

            # Longer delay between chunks to let connections close
            if chunk_end < len(whitelisted_ids):
                if show_progress:
                    print("[gmail_collector] Cooling down for 2s...")
                time.sleep(2.0)

        if show_progress:
            print(f"\n[gmail_collector] PHASE B complete — {len(results)} messages fetched\n")

        return {
            "source": "gmail",
            "total_messages": len(results),
            "messages": results,
        }