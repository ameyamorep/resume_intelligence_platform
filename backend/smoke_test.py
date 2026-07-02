"""End-to-end pipeline smoke test (no server, no API key needed)."""
import json

SAMPLE_RESUME = """Jane Candidate
Sydney, NSW | jane.candidate@email.com | +61 400 123 456
linkedin.com/in/janecandidate | github.com/janecand

Summary
Software engineer with 3 years building data-heavy web products in Python and React.

Experience
Software Engineer | Acme Analytics
Jul 2022 - Present
- Built a FastAPI microservice processing 2M events/day, reducing pipeline latency by 40%
- Led migration of the reporting dashboard to React and TypeScript, improving load time by 60%
- Mentored 2 interns and coordinated a 4-person feature squad

Junior Developer | DataWorks
Jan 2021 - Jun 2022
- Developed ETL jobs in Python and SQL for a Snowflake warehouse
- Responsible for maintaining legacy PHP endpoints

Education
Master of Information Technology, University of Technology Sydney, 2022
Bachelor of Computer Science, University of Pune, 2019

Projects
Resume Ranker | Python, scikit-learn
- Trained a TF-IDF ranking model on 10k resumes achieving 0.82 AUC

Skills
Python, TypeScript, React, FastAPI, SQL, PostgreSQL, Docker, AWS, Git, Pandas

Certifications
AWS Certified Cloud Practitioner
"""

SAMPLE_JD = """Senior Software Engineer - Data Platform

We are looking for an engineer to build our data platform.

Requirements:
- 3+ years of experience in Python backend development
- Strong experience with FastAPI or Django and REST APIs
- Proficiency with SQL and PostgreSQL
- Experience with Docker and Kubernetes
- Must have AWS experience

Nice to have:
- React or Next.js exposure
- Terraform, CI/CD pipelines
- Kafka experience preferred
"""


def main() -> None:
    from app.services.orchestrator import run_analysis

    result = run_analysis("jane_resume.txt", SAMPLE_RESUME.encode(), SAMPLE_JD)

    assert result.resume.contact.email == "jane.candidate@email.com"
    assert result.resume.experience, "no experience parsed"
    assert result.resume.skills, "no skills parsed"
    assert result.ats.total_score > 0
    assert 0 <= result.scores.overall_match <= 100
    assert any(m.name == "Kubernetes" for m in result.skills.missing), "K8s should be missing"
    assert any(m.name == "Python" for m in result.skills.matched), "Python should match"
    assert result.actions, "no actions generated"
    assert result.timeline, "no timeline entries"

    print("PIPELINE OK")
    print(f"  backend            : {result.meta.embedding_backend}")
    print(f"  overall match      : {result.scores.overall_match}")
    print(f"  semantic match     : {result.scores.semantic_match}")
    print(f"  skills coverage    : {result.skills.coverage_pct}%")
    print(f"  ats                : {result.ats.total_score}/{result.ats.max_score}")
    print(f"  matched skills     : {[m.name for m in result.skills.matched]}")
    print(f"  missing skills     : {[m.name for m in result.skills.missing]}")
    print(f"  roles parsed       : {[(e.title, e.company, e.start, e.end) for e in result.resume.experience]}")
    print(f"  actions            : {len(result.actions)} "
          f"({sum(1 for a in result.actions if a.priority == 'high')} high)")
    print(f"  ai                 : {result.meta.ai_available} ({result.meta.ai_error})")
    radar = result.radar.model_dump()
    print("  radar              : " + json.dumps(radar))


if __name__ == "__main__":
    main()
