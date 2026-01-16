# API Documentation

## Base Configuration
- **Host**: `http://localhost:5000` (Default deployment port)
- **Content-Type**: All `POST` requests use `application/x-www-form-urlencoded`
- **Rate Limit**: 60 seconds between OTP requests per email
- **OTP Validity**: 10 minutes
- **Max Attempts**: 5 per OTP session

---

## 1. Request Verification OTP
Triggers the generation and delivery of a 6-digit OTP to the specified email address.

**Endpoint**: `POST /verify`

### Request Parameters (Form Data)
| Field | Type | Description |
| :--- | :--- | :--- |
| `email` | `string` | User's educational email address. |
| `username` | `string` | User's Discord username (Case-sensitive). |

### Responses

#### 200 OK
OTP generated and email sent successfully.
```json
{
  "message": "OTP sent successfully"
}
```

#### 400 Bad Request
- **Email already verified**: The email is already linked to a Discord account.
  ```json
  { "detail": "Email already verified" }
  ```
- **Invalid Domain**: Triggered if `PRODUCTION=true` and email does not end with the allowed BITS domains.
  ```json
  { "detail": "Email must end with @online.bits-pilani.ac.in, @pilani.bits-pilani.ac.in, @hyderabad.bits-pilani.ac.in, @goa.bits-pilani.ac.in, or @dubai.bits-pilani.ac.in" }
  ```

#### 429 Too Many Requests
User must wait for the 60-second cooldown period before requesting another OTP.
```json
{
  "detail": "Please wait 1 minute before requesting another OTP"
}
```

#### 500 Internal Server Error
Resend API failure or server misconfiguration.
```json
{
  "detail": "Failed to send email: <error_details>"
}
```

---

## 2. Check Verification Status
Checks the current state of an email address in the system.

**Endpoint**: `GET /verify/status/{email}`

### Path Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `email` | `string` | The email address to query. |

### Responses

#### 200 OK
- **Case A: Verified User**
  The user has successfully completed verification.
  ```json
  {
    "status": "verified",
    "uid": "123456789012345678",
    "verified_at": "2024-01-15T12:00:00.000000"
  }
  ```
- **Case B: Pending Verification**
  An OTP has been sent and is still valid.
  ```json
  {
    "status": "pending",
    "expiry": 1705323600
  }
  ```
- **Case C: Not Found**
  No record exists, or the previously sent OTP has expired.
  ```json
  {
    "status": "not_found"
  }
  ```

---

## 3. Submit OTP
Validates the OTP and, if correct, grants the Discord role.

**Endpoint**: `POST /verify/otp`

### Request Parameters (Form Data)
| Field | Type | Description |
| :--- | :--- | :--- |
| `email` | `string` | The email address provided in Step 1. |
| `username` | `string` | The Discord username provided in Step 1. |
| `otp` | `string` | The 6-digit code received via email. |

### Responses

#### 200 OK
- **Case A: Success**
  OTP is correct and Discord role was successfully added.
  ```json
  {
    "message": "OTP is correct, user verified on Discord"
  }
  ```
- **Case B: Incorrect OTP (Retry Available)**
  The OTP entered was wrong, but the attempt limit hasn't been reached.
  ```json
  {
    "message": "OTP is incorrect. 4 attempts remaining."
  }
  ```

#### 400 Bad Request
- **No OTP requested**: No pending verification session for this email.
  ```json
  { "detail": "No OTP requested for this email" }
  ```
- **OTP Expired**: The session has timed out (10-minute limit).
  ```json
  { "detail": "OTP has expired" }
  ```
- **Duplicate Discord Link**: This Discord user ID is already linked to another email address.
  ```json
  { "detail": "Discord account already linked to another email" }
  ```
- **Max Attempts Reached**: 5 failed attempts reached; the session is destroyed.
  ```json
  { "detail": "Too many failed attempts. Please request a new OTP." }
  ```

#### 401 Unauthorized
The `otp` field was sent empty.
```json
{
  "detail": "Incorrect OTP!"
}
```

#### 500 Internal Server Error
The Discord bot process failed to respond, find the user in the server, or lacked permissions to add the role.
```json
{
  "detail": "Failed to verify Discord user"
}
```
