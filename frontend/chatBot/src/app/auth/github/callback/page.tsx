"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function GitHubCallbackPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
    const [message, setMessage] = useState("Processing GitHub connection...");

    useEffect(() => {
        const installationId = searchParams.get("installation_id");
        const setupAction = searchParams.get("setup_action");

        if (installationId) {
            // Success - GitHub App installed
            setStatus("success");
            setMessage("GitHub connected successfully!");

            // Redirect to pipeline page after 2 seconds
            setTimeout(() => {
                router.push("/manager/pipeline?github_connected=true&installation_id=" + installationId);
            }, 2000);
        } else {
            // No installation_id - something went wrong
            setStatus("error");
            setMessage("Failed to connect GitHub. Please try again.");

            // Redirect back to pipeline after 3 seconds
            setTimeout(() => {
                router.push("/manager/pipeline");
            }, 3000);
        }
    }, [searchParams, router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800">
            <div className="max-w-md w-full mx-4">
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 text-center">
                    {status === "loading" && (
                        <>
                            <Loader2 className="w-16 h-16 animate-spin text-blue-500 mx-auto mb-4" />
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                                Connecting GitHub...
                            </h2>
                            <p className="text-gray-600 dark:text-gray-400">{message}</p>
                        </>
                    )}

                    {status === "success" && (
                        <>
                            <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle2 className="w-10 h-10 text-emerald-600 dark:text-emerald-400" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                                Success!
                            </h2>
                            <p className="text-gray-600 dark:text-gray-400 mb-4">{message}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-500">
                                Redirecting to pipeline...
                            </p>
                        </>
                    )}

                    {status === "error" && (
                        <>
                            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                                <AlertCircle className="w-10 h-10 text-red-600 dark:text-red-400" />
                            </div>
                            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                                Connection Failed
                            </h2>
                            <p className="text-gray-600 dark:text-gray-400 mb-4">{message}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-500">
                                Redirecting back...
                            </p>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
