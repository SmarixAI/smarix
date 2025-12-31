export interface ValidationResult {
  isValid: boolean;
  error?: string;
}

/**
 * Validates GitHub organization or repository name
 * Rules:
 * - Must be 1-39 characters
 * - Can contain alphanumeric characters and hyphens
 * - Cannot start or end with a hyphen
 * - Cannot contain spaces or special characters (except hyphens)
 * - Cannot be empty or just whitespace
 */
export function validateGitHubName(name: string, fieldName: string): ValidationResult {
  const trimmed = name.trim();

  // Check if empty
  if (!trimmed) {
    return {
      isValid: false,
      error: `${fieldName} cannot be empty`,
    };
  }

  // Check length (GitHub allows 1-39 characters for org/repo names)
  if (trimmed.length < 1) {
    return {
      isValid: false,
      error: `${fieldName} must be at least 1 character`,
    };
  }

  if (trimmed.length > 39) {
    return {
      isValid: false,
      error: `${fieldName} must be 39 characters or less`,
    };
  }

  // Check for invalid characters (only alphanumeric and hyphens allowed)
  if (!/^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$/.test(trimmed)) {
    return {
      isValid: false,
      error: `${fieldName} can only contain letters, numbers, and hyphens. Cannot start or end with a hyphen.`,
    };
  }

  // Check if starts or ends with hyphen
  if (trimmed.startsWith("-") || trimmed.endsWith("-")) {
    return {
      isValid: false,
      error: `${fieldName} cannot start or end with a hyphen`,
    };
  }

  // Check for consecutive hyphens (optional, but good practice)
  if (trimmed.includes("--")) {
    return {
      isValid: false,
      error: `${fieldName} cannot contain consecutive hyphens`,
    };
  }

  return { isValid: true };
}

/**
 * Validates both organization and repository names
 */
export function validateRepositoryInput(organization: string, repoName: string): {
  isValid: boolean;
  orgError?: string;
  repoError?: string;
} {
  const orgValidation = validateGitHubName(organization, "Organization name");
  const repoValidation = validateGitHubName(repoName, "Repository name");

  return {
    isValid: orgValidation.isValid && repoValidation.isValid,
    orgError: orgValidation.error,
    repoError: repoValidation.error,
  };
}

