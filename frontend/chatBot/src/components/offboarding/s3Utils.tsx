import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';

const S3_BUCKET = 'smarix-data-apsouth1';
const S3_BASE_PATH = 'Offboarding';

// Initialize S3 Client
const s3Client = new S3Client({
  region: process.env.AWS_DEFAULT_REGION || 'ap-south-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
  },
});

/**
 * Build S3 key, optionally under an employee folder (Offboarding/{employeeId}/fileName).
 */
export function getOffboardingKey(fileName: string, employeeId?: string | null): string {
  if (employeeId?.trim()) {
    return `${S3_BASE_PATH}/${encodeURIComponent(employeeId.trim())}/${fileName}`;
  }
  return `${S3_BASE_PATH}/${fileName}`;
}

/**
 * Build S3 key under employee folder and a subfolder (e.g. Offboarding/{employeeId}/upload/{fileName}).
 */
export function getOffboardingKeyWithSubfolder(
  employeeId: string,
  subfolder: string,
  fileName: string
): string {
  const safeId = employeeId?.trim() ? encodeURIComponent(employeeId.trim()) : '';
  const safeSub = subfolder.replace(/\/|\.\./g, '');
  return `${S3_BASE_PATH}/${safeId}/${safeSub}/${fileName}`;
}

/**
 * Upload a raw file (e.g. .txt) to S3 under Offboarding/{employeeId}/{subfolder}/{fileName}.
 */
export async function uploadFileToS3(
  employeeId: string,
  subfolder: string,
  fileName: string,
  body: Buffer | Uint8Array,
  contentType: string
): Promise<void> {
  const key = getOffboardingKeyWithSubfolder(employeeId, subfolder, fileName);
  try {
    await s3Client.send(
      new PutObjectCommand({
        Bucket: S3_BUCKET,
        Key: key,
        Body: body,
        ContentType: contentType,
      })
    );
  } catch (error) {
    console.error(`Error uploading ${fileName} to S3:`, error);
    throw error;
  }
}

/**
 * Read a raw file from S3 (e.g. .txt) from Offboarding/{employeeId}/{subfolder}/{fileName}.
 * Returns Buffer (for .txt uses UTF-8 string then Buffer).
 */
export async function readFileFromS3(
  employeeId: string,
  subfolder: string,
  fileName: string
): Promise<Buffer> {
  const key = getOffboardingKeyWithSubfolder(employeeId, subfolder, fileName);
  const command = new GetObjectCommand({ Bucket: S3_BUCKET, Key: key });
  const response = await s3Client.send(command);
  const bodyString = await response.Body?.transformToString('utf-8');
  if (bodyString == null) throw new Error('Empty response from S3');
  return Buffer.from(bodyString, 'utf-8');
}

/**
 * Read JSON file from S3
 */
export async function readJsonFromS3(fileName: string, employeeId?: string | null): Promise<any> {
  const key = getOffboardingKey(fileName, employeeId);
  
  try {
    const command = new GetObjectCommand({
      Bucket: S3_BUCKET,
      Key: key,
    });

    const response = await s3Client.send(command);
    const bodyString = await response.Body?.transformToString();
    
    if (!bodyString) {
      throw new Error('Empty response from S3');
    }

    return JSON.parse(bodyString);
  } catch (error) {
    console.error(`Error reading ${fileName} from S3:`, error);
    throw error;
  }
}

/**
 * Write JSON file to S3 (optionally under employee folder).
 */
export async function writeJsonToS3(fileName: string, data: any, employeeId?: string | null): Promise<void> {
  const key = getOffboardingKey(fileName, employeeId);
  
  try {
    const command = new PutObjectCommand({
      Bucket: S3_BUCKET,
      Key: key,
      Body: JSON.stringify(data, null, 2),
      ContentType: 'application/json',
    });

    await s3Client.send(command);
  } catch (error) {
    console.error(`Error writing ${fileName} to S3:`, error);
    throw error;
  }
}

/**
 * Try multiple file names and return the first one that exists.
 * If employeeId is provided, reads from Offboarding/{employeeId}/fileName.
 */
export async function readJsonFromS3WithFallback(
  fileNames: string[],
  employeeId?: string | null
): Promise<{ data: any; fileName: string }> {
  for (const fileName of fileNames) {
    try {
      const data = await readJsonFromS3(fileName, employeeId);
      return { data, fileName };
    } catch (error) {
      continue;
    }
  }
  const prefix = employeeId ? `Offboarding/${employeeId}/` : 'Offboarding/';
  throw new Error(`None of the files found in S3: ${fileNames.map((f) => prefix + f).join(', ')}`);
}
