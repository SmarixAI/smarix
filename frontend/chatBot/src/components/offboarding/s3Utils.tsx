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
