"""Curated technical-skill taxonomy with alias normalization.

Canonical name -> aliases. Matching is word-boundary based and
case-insensitive; aliases cover common spellings ("golang", "node js",
"scikit learn"). Extend freely — everything downstream uses canonical names.
"""
from __future__ import annotations

import re

TAXONOMY: dict[str, list[str]] = {
    # Languages
    "Python": ["python", "python3"],
    "Java": ["java"],
    "JavaScript": ["javascript", "es6"],
    "TypeScript": ["typescript"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp", ".net", "dotnet"],
    "Go": ["golang", "go"],
    "Rust": ["rust"],
    "Ruby": ["ruby", "rails", "ruby on rails"],
    "PHP": ["php", "laravel"],
    "Swift": ["swift"],
    "Kotlin": ["kotlin"],
    "R": ["r programming", "rstudio"],
    "Scala": ["scala"],
    "SQL": ["sql", "t-sql", "pl/sql"],
    "Bash": ["bash", "shell scripting", "shell"],
    "MATLAB": ["matlab"],
    # Frontend
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs", "next js"],
    "Vue.js": ["vue", "vue.js", "vuejs", "nuxt"],
    "Angular": ["angular", "angularjs"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3", "sass", "scss"],
    "Tailwind CSS": ["tailwind", "tailwindcss", "tailwind css"],
    "Redux": ["redux"],
    # Backend / frameworks
    "Node.js": ["node", "node.js", "nodejs", "node js", "express", "express.js"],
    "FastAPI": ["fastapi", "fast api"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Spring Boot": ["spring", "spring boot", "springboot"],
    "GraphQL": ["graphql"],
    "REST APIs": ["rest", "rest api", "restful", "rest apis", "restful apis"],
    "gRPC": ["grpc"],
    "Microservices": ["microservices", "micro-services", "microservice"],
    # Data / ML
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "neural networks", "neural network"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "opencv", "cv"],
    "TensorFlow": ["tensorflow", "tf", "keras"],
    "PyTorch": ["pytorch", "torch"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Spark": ["spark", "pyspark", "apache spark"],
    "Hadoop": ["hadoop"],
    "Airflow": ["airflow", "apache airflow"],
    "dbt": ["dbt"],
    "LLMs": ["llm", "llms", "large language models", "gpt", "claude", "generative ai", "genai", "gen ai"],
    "Data Analysis": ["data analysis", "data analytics", "analytics"],
    "Data Engineering": ["data engineering", "etl", "elt", "data pipelines", "data pipeline"],
    "Data Visualization": ["data visualization", "data visualisation", "matplotlib", "seaborn"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "Excel": ["excel", "microsoft excel"],
    "Statistics": ["statistics", "statistical analysis", "statistical modeling"],
    "A/B Testing": ["a/b testing", "ab testing", "experimentation"],
    # Databases
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "opensearch"],
    "DynamoDB": ["dynamodb"],
    "Snowflake": ["snowflake"],
    "BigQuery": ["bigquery", "big query"],
    "SQLite": ["sqlite"],
    "Oracle": ["oracle db", "oracle database"],
    "Kafka": ["kafka", "apache kafka"],
    "RabbitMQ": ["rabbitmq"],
    # Cloud / DevOps
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Docker": ["docker", "containers", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform", "infrastructure as code", "iac"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "continuous deployment", "jenkins", "github actions", "gitlab ci"],
    "Linux": ["linux", "unix", "ubuntu"],
    "Git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "Monitoring": ["prometheus", "grafana", "datadog", "observability", "monitoring"],
    "Serverless": ["serverless"],
    # Testing / practice
    "Unit Testing": ["unit testing", "unit tests", "pytest", "jest", "junit", "test-driven", "tdd"],
    "Agile": ["agile", "scrum", "kanban", "sprint"],
    "System Design": ["system design", "distributed systems", "scalable systems", "scalability"],
    "Security": ["security", "oauth", "authentication", "authorization", "owasp"],
    # Soft-ish but commonly required
    "Communication": ["communication skills", "stakeholder management", "stakeholder"],
    "Leadership": ["leadership", "team leadership", "mentoring", "mentorship"],
    "Problem Solving": ["problem solving", "problem-solving"],
    "Project Management": ["project management", "jira", "confluence"],
}

_ALIAS_PATTERNS: list[tuple[str, re.Pattern]] = []


def _patterns() -> list[tuple[str, re.Pattern]]:
    global _ALIAS_PATTERNS
    if not _ALIAS_PATTERNS:
        pats = []
        for canonical, aliases in TAXONOMY.items():
            for alias in sorted(aliases, key=len, reverse=True):
                esc = re.escape(alias).replace(r"\ ", r"[\s-]?")
                pats.append((canonical, re.compile(rf"(?<![\w+#]){esc}(?![\w+])", re.I)))
        _ALIAS_PATTERNS = pats
    return _ALIAS_PATTERNS


def find_skills(text: str) -> set[str]:
    """Return the set of canonical skills mentioned anywhere in `text`."""
    found: set[str] = set()
    for canonical, pattern in _patterns():
        if canonical not in found and pattern.search(text):
            found.add(canonical)
    return found
