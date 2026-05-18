from django.contrib.auth import get_user_model
from apps.core.models import Role, BlogPost, DocumentationPage
from django.utils.text import slugify
from django.utils import timezone

User = get_user_model()

def seed_data():
    # 0. Ensure Roles exist
    admin_role, _ = Role.objects.get_or_create(name=Role.Name.ADMIN)
    user_role, _ = Role.objects.get_or_create(name=Role.Name.USER)
    print("Roles ensured")

    # 1. Create Admin User
    admin_email = "admin@guardly.com"
    admin_user, created = User.objects.get_or_create(
        email=admin_email,
        defaults={
            "username": "admin",
            "is_staff": True,
            "is_superuser": True,
            "role": admin_role
        }
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print(f"Admin created: {admin_email} / admin123")
    else:
        print(f"Admin already exists: {admin_email}")

    # 2. Create Regular User
    user_email = "user@guardly.com"
    reg_user, created = User.objects.get_or_create(
        email=user_email,
        defaults={
            "username": "user",
            "is_staff": False,
            "is_superuser": False,
            "role": user_role
        }
    )
    if created:
        reg_user.set_password("user123")
        reg_user.save()
        print(f"User created: {user_email} / user123")
    else:
        print(f"User already exists: {user_email}")

    # 3. Create Blog Posts
    blogs = [
        {
            "title": "Understanding the OWASP Top 10 in 2026",
            "content": "A deep dive into the most critical web application security risks and how to mitigate them using modern tools. In this article, we explore how injection, broken access control, and cryptographic failures continue to dominate the security landscape.",
            "tags": "OWASP, Security, Tutorial",
        },
        {
            "title": "How to Secure Your RESTful APIs with JWT",
            "content": "Best practices for implementing JSON Web Tokens (JWT) for secure authentication in your backend applications. We cover token signing, expiration policies, and secure storage.",
            "tags": "API, JWT, Auth",
        },
        {
            "title": "Real-World Examples of SQL Injection Attacks",
            "content": "Learning from history: a breakdown of famous data breaches caused by simple SQL injection vulnerabilities. We analyze the technical details of past exploits and how they could have been prevented.",
            "tags": "Exploits, SQLi, Case Study",
        }
    ]

    for b in blogs:
        slug = slugify(b["title"])
        BlogPost.objects.get_or_create(
            slug=slug,
            defaults={
                "author": admin_user,
                "title": b["title"],
                "content": b["content"],
                "tags": b["tags"],
                "status": BlogPost.Status.PUBLISHED,
                "published_at": timezone.now()
            }
        )
    print(f"Ensured {len(blogs)} blog posts")

    # 4. Create Documentation Pages
    docs = [
        {
            "title": "How Web Security Works",
            "category": "Introduction",
            "content": "Web security is a critical part of any modern application. Understanding how to protect your data and your users is the first step toward building a reliable platform. Guardly uses advanced scanning algorithms to detect vulnerabilities in real-time.",
        },
        {
            "title": "Vulnerability Scanning",
            "category": "Introduction",
            "content": "Vulnerability scanning is the process of identifying, evaluating, and prioritizing security weaknesses in a system or network. Our platform automates this process, providing you with detailed reports and remediation steps.",
        },
        {
            "title": "OWASP Top 10 Breakdown",
            "category": "Core Concepts",
            "content": "The OWASP Top 10 is a standard awareness document for developers and web application security. It represents a broad consensus about the most critical security risks to web applications.",
        }
    ]

    for d in docs:
        slug = slugify(d["title"])
        DocumentationPage.objects.get_or_create(
            slug=slug,
            defaults={
                "title": d["title"],
                "category": d["category"],
                "content": d["content"],
                "is_published": True
            }
        )
    print(f"Ensured {len(docs)} documentation pages")

seed_data()
