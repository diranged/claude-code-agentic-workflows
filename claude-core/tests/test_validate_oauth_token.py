#!/usr/bin/env python3
"""Tests for OAuth token expiry detection script."""

import base64
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


class TestValidateOAuthToken(unittest.TestCase):
    """Test OAuth token validation script."""

    def setUp(self):
        """Set up test environment."""
        # Get the script path
        self.script_dir = Path(__file__).parent.parent / "scripts"
        self.script_path = self.script_dir / "validate_oauth_token.sh"

        # Ensure script exists and is executable
        self.assertTrue(self.script_path.exists(), f"Script not found: {self.script_path}")
        self.assertTrue(os.access(self.script_path, os.X_OK), f"Script not executable: {self.script_path}")

    def run_script(self, oauth_token=None):
        """Run the validation script with given OAuth token."""
        env = os.environ.copy()
        if oauth_token is not None:
            env["OAUTH_TOKEN"] = oauth_token
        elif "OAUTH_TOKEN" in env:
            del env["OAUTH_TOKEN"]

        try:
            result = subprocess.run(
                [str(self.script_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            self.fail(f"Failed to run script: {e}")

    def create_jwt_token(self, exp_claim=None, include_exp=True):
        """Create a test JWT token with optional expiry claim."""
        # Header
        header = {"alg": "HS256", "typ": "JWT"}
        header_encoded = base64.urlsafe_b64encode(
            json.dumps(header, separators=(',', ':')).encode()
        ).decode().rstrip("=")

        # Payload
        payload = {"sub": "test"}
        if include_exp and exp_claim is not None:
            payload["exp"] = exp_claim
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(',', ':')).encode()
        ).decode().rstrip("=")

        # Signature (fake - just for testing format)
        signature = base64.urlsafe_b64encode(b"fake_signature").decode().rstrip("=")

        return f"{header_encoded}.{payload_encoded}.{signature}"

    def test_no_oauth_token(self):
        """Test script exits successfully when no OAuth token is provided."""
        returncode, stdout, stderr = self.run_script(oauth_token=None)
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_empty_oauth_token(self):
        """Test script exits successfully when OAuth token is empty."""
        returncode, stdout, stderr = self.run_script(oauth_token="")
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_non_jwt_token(self):
        """Test script skips validation for non-JWT tokens."""
        returncode, stdout, stderr = self.run_script(oauth_token="simple_token_without_dots")
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_malformed_jwt_token(self):
        """Test script handles malformed JWT tokens gracefully."""
        malformed_tokens = [
            "header.payload",  # Missing signature
            "header..signature",  # Empty payload
            "header.invalid_base64.signature",  # Invalid base64 in payload
        ]

        for token in malformed_tokens:
            with self.subTest(token=token):
                returncode, stdout, stderr = self.run_script(oauth_token=token)
                self.assertEqual(returncode, 0, f"Script should not fail for malformed token: {token}")

    def test_jwt_without_exp_claim(self):
        """Test JWT without exp claim is skipped."""
        token = self.create_jwt_token(include_exp=False)
        returncode, stdout, stderr = self.run_script(oauth_token=token)
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_valid_jwt_not_expired(self):
        """Test valid JWT that is not expired."""
        # Token expires 1 hour from now
        future_exp = int(time.time()) + 3600
        token = self.create_jwt_token(exp_claim=future_exp)
        returncode, stdout, stderr = self.run_script(oauth_token=token)
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

    def test_expired_jwt_token(self):
        """Test expired JWT token triggers error."""
        # Token expired 1 hour ago
        past_exp = int(time.time()) - 3600
        token = self.create_jwt_token(exp_claim=past_exp)
        returncode, stdout, stderr = self.run_script(oauth_token=token)
        self.assertEqual(returncode, 1)
        self.assertIn("::error::OAuth token has expired", stderr)
        self.assertIn("claude setup-token", stderr)

    def test_jwt_near_expiry_warning(self):
        """Test JWT near expiry triggers warning."""
        # Token expires in 2 minutes
        near_exp = int(time.time()) + 120
        token = self.create_jwt_token(exp_claim=near_exp)
        returncode, stdout, stderr = self.run_script(oauth_token=token)
        self.assertEqual(returncode, 0)
        self.assertIn("::warning::OAuth token expires in", stderr)
        self.assertIn("claude setup-token", stderr)

    def test_jwt_far_future_expiry(self):
        """Test JWT with far future expiry."""
        # Token expires in 1 year
        far_future_exp = int(time.time()) + (365 * 24 * 60 * 60)
        token = self.create_jwt_token(exp_claim=far_future_exp)
        returncode, stdout, stderr = self.run_script(oauth_token=token)
        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()