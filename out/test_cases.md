# Test Cases

## TC-001 - Test TC-001
### Objective
Verify user is navigated to the dashboard
### Preconditions
- User is on the login screen
### Steps
1. Enter a valid email address
1. Enter a valid password
1. Click the Sign In button
### Expected Result
User is navigated to the dashboard
### Priority: High

## TC-002 - Test TC-002
### Objective
Verify error message is displayed for invalid email format
### Preconditions
- User is on the login screen
### Steps
1. Enter an invalid email address
1. Enter a valid password
1. Click the Sign In button
### Expected Result
Error message is displayed for invalid email format
### Priority: High

## TC-003 - Test TC-003
### Objective
Verify error message is displayed for incorrect password
### Preconditions
- User is on the login screen
### Steps
1. Enter a valid email address
1. Enter an incorrect password
1. Click the Sign In button
### Expected Result
Error message is displayed for incorrect password
### Priority: High

## TC-004 - Test TC-004
### Objective
Verify error message is displayed for blank password
### Preconditions
- User is on the login screen
### Steps
1. Enter a valid email address
1. Leave the password field blank
1. Click the Sign In button
### Expected Result
Error message is displayed for blank password
### Priority: Medium

## TC-005 - Test TC-005
### Objective
Verify user is navigated to the password recovery page
### Preconditions
- User is on the login screen
### Steps
1. Click the Forgot password? link
### Expected Result
User is navigated to the password recovery page
### Priority: Medium

## TC-006 - Test TC-006
### Objective
Verify password strength hint is displayed
### Preconditions
- User is on the login screen
### Steps
1. Enter a valid email address with a weak password
1. Click the Sign In button
### Expected Result
Password strength hint is displayed
### Priority: Low

## TC-007 - Test TC-007
### Objective
Verify no password strength hint is displayed
### Preconditions
- User is on the login screen
### Steps
1. Enter a valid email address with a strong password
1. Click the Sign In button
### Expected Result
No password strength hint is displayed
### Priority: Low
