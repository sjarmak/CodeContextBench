# Encryption at Rest Audit: Key Management and Encrypted Database Fields

## Your Task

Our compliance team needs to verify that all sensitive data stored in the Sourcegraph database is encrypted at rest. Map the encryption key management system: what key types are supported, how keys are configured and rotated, which database fields use encrypted storage, and what happens if encryption is disabled (noop mode).

## Context

Sourcegraph uses an encryption abstraction layer (the relevant code area) supporting multiple key management backends (AES, RSA, AWS KMS, GCP Cloud KMS, mounted keys). The keyring pattern provides global access to encryption keys, and generic `Encryptable` wrappers handle encrypted database fields.

## Available Resources

No local repositories are pre-checked out.

## Task Contract

- `TASK_WORKDIR=/workspace`
- `TASK_REPO_ROOT=/workspace`
- `TASK_OUTPUT=/workspace/answer.json`

## Output Format

Create a file at `/workspace/answer.json` (`TASK_OUTPUT`) with your findings in the following structure:

```json
{
  "files": [
    {
      "repo": "sourcegraph/sourcegraph",
      "path": "relative/path/to/file.go"
    }
  ],
  "symbols": [
    {
      "repo": "sourcegraph/sourcegraph",
      "path": "relative/path/to/file.go",
      "symbol": "SymbolName"
    }
  ],
  "chain": [
    {
      "repo": "sourcegraph/sourcegraph",
      "path": "relative/path/to/file.go",
      "symbol": "FunctionName"
    }
  ],
  "summary": "Brief explanation of the encryption architecture and key management system"
}
```

Include ALL files that define encryption keys, implement key backends, provide the keyring, wrap database fields, or configure encryption settings.
