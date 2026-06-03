# GitHub Quick Reference Guide
## Track 4: Performance & Scalability RAG Capstone

---

## 🚀 QUICK START (First 30 minutes)

### 1. Clone & Setup
```bash
git clone https://github.com/team/enterprise-rag-capstone.git
cd enterprise-rag-capstone

# Checkout your feature branch
git checkout -b feature/[your-scope]  # M1: ingestion-pipeline, M2: hybrid-search, etc.

# Verify everything works
docker-compose up -d
curl http://localhost:8000/health  # Backend
curl http://localhost:3000          # Frontend
```

### 2. Create Commits (Throughout Your Work)
```bash
git add backend/app/[your-module]/file.py
git commit -m "feat([scope]): add [what you did] (#[issue-id])"
# Examples:
# feat(ingestion): add SemanticChunker class (#1)
# feat(search): implement RRF fusion algorithm (#2)
# feat(cache): add 3-layer Redis caching with TTL (#3)
```

### 3. Push & Create PR (When Done)
```bash
git push -u origin feature/[your-scope]
# Go to GitHub → Create Pull Request
# Title: [M1] Your Feature Name
# Description: (use PR template)
# Reviewers: Pick 2 team members
```

### 4. Merge (After Approval)
```bash
# GitHub: Click "Merge" button
# OR via CLI:
git checkout develop
git pull origin develop
git merge feature/[your-scope] --squash
git commit -m "feat([scope]): [your feature summary] (#[issue-id])"
git push origin develop

# Cleanup
git branch -d feature/[your-scope]
git push origin --delete feature/[your-scope]
```

---

## 📊 BRANCH STRUCTURE

```
main (v1.0.0)
  ↑
  Merge at milestones (0:30, 3:00, 4:00)
  
develop (integration)
  ↑
  All PRs merge here
  
  ├─ feature/ingestion-pipeline (M1)
  ├─ feature/hybrid-search (M2)
  ├─ feature/generation-guardrails (M3)
  ├─ feature/caching-performance (M4)
  └─ feature/frontend-ui (M5)
```

---

## 📝 COMMIT MESSAGE TEMPLATES

### Feature Commit
```
feat(scope): add [what it does] (#[issue])

Detailed explanation of why and what (not how).
Use imperative mood. Wrap at 72 chars.

Closes #[issue]

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Example: Semantic Chunking
```
feat(ingestion): add semantic chunking with section detection (#1)

Implement SemanticChunker class that detects paragraph and section
boundaries instead of fixed-size token splitting. Improves retrieval
accuracy by 25% on benchmark.

- Uses section headers to detect boundaries
- Preserves paragraph breaks
- Overlaps 50 tokens between chunks
- Reduces token inflation from 10K → 2.5K

Closes #1

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## ✅ PRE-MERGE CHECKLIST

Before requesting review:
- [ ] `git pull origin develop` (sync with latest)
- [ ] All unit tests pass locally: `pytest tests/`
- [ ] No conflicts with develop
- [ ] Commits follow conventional commit format
- [ ] PR title matches: `[M#] Description`
- [ ] PR description filled (use template)
- [ ] Reviewers assigned (pick 2)

---

## 🔄 SYNC POINTS & MERGES

### Sync 1 (0:30)
- [ ] All members cloned repo
- [ ] All feature branches created from develop
- [ ] Docker services verified running
- [ ] API contracts agreed (Section 4 of plan)

### Sync 2 (1:45) — First Merge
```bash
# M1 is ready first, merges to develop
git checkout develop && git pull
git merge feature/ingestion-pipeline --squash
git commit -m "feat(ingestion): complete document ingestion"
git push origin develop
```

### Sync 3 (3:00) — All Features Merge
```bash
# M2, M3, M4, M5 merge in order
# Each creates PR, gets review, merges

# Then merge develop → main
git checkout main && git pull
git merge develop --no-ff -m "Milestone: v0.5.0 - All features integrated"
git push origin main
git tag v0.5.0 && git push origin v0.5.0
```

### Final (3:50–4:00) — Production Release
```bash
# Docs, final commit, v1.0.0 tag
git checkout main
git add docs/
git commit -m "docs: add architecture and final analysis"
git push origin main
git tag v1.0.0 -m "Release v1.0.0 - Production RAG capstone"
git push origin v1.0.0
```

---

## 🐛 IF MERGE CONFLICTS HAPPEN

**Conflict Resolution Steps:**
```bash
# 1. Stop other merges (notify Slack)
# 2. Conflict owner fetches latest develop
git fetch origin
git rebase origin/develop
# or
git merge origin/develop

# 3. Resolve conflicts manually
# Edit files with <<< >>> markers

# 4. Mark resolved
git add [resolved-files]
git rebase --continue  # if rebased
# or
git commit -m "Merge conflict resolved"  # if merged

# 5. Test again
pytest tests/

# 6. Push (with -f if rebased)
git push origin feature/[scope] -f

# 7. Re-request review
```

---

## 📋 FILE OWNERSHIP (NO OVERLAPS)

```
backend/
├── app/
│   ├── ingestion/          ← M1 ONLY
│   ├── search/             ← M2 ONLY
│   ├── generation/         ← M3 ONLY
│   ├── cache/              ← M4 ONLY
│   ├── api/                ← ALL (but split by feature)
│   └── models/schemas.py   ← SHARED (coordinate)

frontend/
├── src/components/         ← M5 ONLY
```

**Rule**: Don't edit another member's files without coordination!

---

## 🎯 EVALUATION CRITERIA MAPPING

| Criterion | Weight | Primary Owner | Demo |
|-----------|--------|---------------|------|
| **Retrieval Accuracy** | 25% | M1 + M2 | Demo 2: Error codes |
| **Production Readiness** | 20% | M4 + M3 | Demo 3: Cache speedup |
| **Architecture Design** | 15% | M5 | Architecture diagram |
| **Hallucination Prevention** | 15% | M3 | Demo 4: Fallback message |
| **Innovation & Bonus** | 25% | All | Demo 5: Compression |

**How to Win Each:**
- **Retrieval (25%)**: Semantic chunking + RRF fusion outperforms vector-only
- **Production (20%)**: <500ms cold, <10ms warm, >70% cache hit rate
- **Architecture (15%)**: Clean file separation, Docker Compose, dependency injection
- **Hallucination (15%)**: Grounding prompt + source citation + fallback message
- **Innovation (25%)**: Semantic chunking + hybrid search + 3-layer cache + streaming + 2 bonus features

---

## 🔍 STATUS COMMANDS

```bash
# Check current branch
git branch -a

# See unpushed commits
git log origin/develop..HEAD

# See uncommitted changes
git status
git diff

# Check develop status
git diff develop

# List all branches with last commit
git branch -v

# See PR status
git log --oneline --all --decorate

# Clean up local branches
git branch -d feature/[scope]  # only after merged
```

---

## 📞 GETTING HELP

**Common Issues:**

```
Q: "I'm ahead of develop and can't merge"
A: git rebase origin/develop (on feature branch)

Q: "I have conflicts with another file"
A: git status → see which files
   Coordinate with owner → resolve together
   git add [files] → git rebase --continue

Q: "I pushed to wrong branch"
A: git push origin +HEAD~1:feature/[branch]  (force to previous commit)
   Or create new branch: git checkout -b feature/[new]

Q: "How do I squash commits?"
A: git rebase -i HEAD~5  (squash last 5)
   Change "pick" → "squash" on commits to squash
   :wq to save

Q: "I want to undo my last commit"
A: git reset --soft HEAD~1  (keep changes staged)
   git reset --hard HEAD~1  (discard changes)
```

---

## ⏰ TIMELINE AT A GLANCE

```
0:00 ──── Clone, setup, sync
0:30 ──── [SYNC 1] Docker verify
0:30–1:30 Parallel coding (M1–M5)
1:30 ──── [SYNC 2] M1 demos, merges
1:45–3:00 Continue coding, enhancements
3:00 ──── [SYNC 3] M2–M5 merge, develop→main
3:20–3:50 Demo rehearsal
3:50–4:00 Final commit, tag v1.0.0
```

---

## ✨ SUCCESS CHECKLIST

Before final submission:
- [ ] All 5 feature branches merged to develop
- [ ] develop merged to main
- [ ] v1.0.0 tag created and pushed
- [ ] All tests passing on main
- [ ] Architecture diagram in docs/
- [ ] README updated with setup instructions
- [ ] All 5 demos rehearsed and working
- [ ] Demo metrics captured (before/after)
- [ ] Clean git history (linear or well-organized)
- [ ] No merge conflicts on main

**You're done when GitHub shows:**
```
main: v1.0.0 ✓
develop: All features merged ✓
CI/CD: All checks passing ✓
PRs: 5 PRs merged (M1–M5) ✓
```

---

**Last Updated**: 2024-06-03  
**Format**: GitHub CLI + Web UI instructions  
**Team**: M1–M5 (5 parallel developers)
