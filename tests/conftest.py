import os

os.environ["ENV_FILE"] = "tests/testing.env"

# Update these per institution
os.environ["BANK_URL"] = "https://example.com/bank"
os.environ["BANK_USER"] = "test_user"
os.environ["BANK_PASSWORD"] = "test_password"
os.environ["BANK_LOGIN_URL"] = "https://example.com/login"
os.environ["BANK_API_BASE_URL"] = "https://api.example.com/bank"

os.environ["HEADER_REFERER"] = "https://example.com/referer"
os.environ["HEADER_ORIGIN"] = "https://example.com/origin"
