# Task Checklist Template

Use this template to structure your implementation plans and checklists when executing tasks on Advice Content Radar.

---

## 1. Goal Description

*Briefly describe what this task achieves, what component is affected, and any key user specifications.*

---

## 2. Implementation Checklist

- [ ] **Data Model & Schema Modifications**
  - [ ] Update models in `app/models/` (if database structures are changing).
  - [ ] Update Pydantic serialization schemas in `app/schemas/`.
  - [ ] Add SQL migrations if needed.
- [ ] **Core Business Services**
  - [ ] Write/modify service logic in `app/services/`.
  - [ ] Handle error scenarios and log output using `logging`.
  - [ ] Ensure MOCK_MODE is respected if mocking external APIs.
- [ ] **API Router Gateways**
  - [ ] Register new path operations or query parameters in `app/routers/`.
  - [ ] Verify access dependencies (`require_admin_api_key_header` etc.) are correctly in place.
- [ ] **Testing & Verification**
  - [ ] Add pytest files under `tests/`.
  - [ ] Perform manual validation commands.

---

## 3. Files to Create/Modify

### [NEW]
* `app/.../new_file.py`

### [MODIFY]
* `app/.../existing_file.py`

---

## 4. Verification Commands

Run these commands locally to verify changes before marking the task complete:

### 1. Run Unit/Integration Tests
```bash
python -m pytest tests -q
```

### 2. Verify Linting & Syntax (Optional)
```bash
python -m flake8 app tests
# Or using another linter setup configured locally
```

### 3. Startup Server Verification
Start the development server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Verify service is responsive:
```bash
python -c "import httpx; print(httpx.get('http://127.0.0.1:8010/health').json())"
```

---

## 5. Git Commit Guidelines

Commit messages should follow standard descriptive formats:
* **Format**: `type(scope): message`
* **Examples**:
  * `feat(collector): add TikTok trend monitoring support`
  * `fix(scoring): prevent division by zero in average score calculation`
  * `docs(readme): update environment variable setup instructions`
