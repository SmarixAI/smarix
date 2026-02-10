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
 * Read JSON file from S3
 */
export async function readJsonFromS3(fileName: string): Promise<any> {
  const key = `${S3_BASE_PATH}/${fileName}`;
  
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
 * Write JSON file to S3
 */
export async function writeJsonToS3(fileName: string, data: any): Promise<void> {
  const key = `${S3_BASE_PATH}/${fileName}`;
  
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
 * Try multiple file names and return the first one that exists
 */
export async function readJsonFromS3WithFallback(fileNames: string[]): Promise<{ data: any; fileName: string }> {
  for (const fileName of fileNames) {
    try {
      const data = await readJsonFromS3(fileName);
      return { data, fileName };
    } catch (error) {
      // Continue to next file
      continue;
    }
  }
  
  throw new Error(`None of the files found in S3: ${fileNames.join(', ')}`);
}
