# Viva Questions and Answers

1. **Why use MVC in Flask?**  
   MVC separates data logic, request logic, and UI, making maintenance and scaling easier.

2. **How is RBAC implemented here?**  
   A `role` field in `users` and `role_required` decorator control endpoint access.

3. **Why bcrypt for passwords?**  
   Bcrypt is adaptive and salted, making brute-force attacks harder.

4. **How do you prevent SQL injection?**  
   SQLAlchemy ORM uses parameterized queries by default.

5. **How is CSRF prevented?**  
   Flask-WTF injects and validates CSRF tokens in forms.

6. **How are marks and grades calculated?**  
   Total = internal + external; grade computed by score thresholds.

7. **How is teacher data isolation ensured?**  
   Teacher actions are limited using `teacher_id` checks against assignments.

8. **How can this be made cloud-ready?**  
   Move to managed MySQL, object storage for files, and containerize with Docker.

9. **How would you add REST APIs?**  
   Add API blueprints with JWT auth and serializers for each module.

10. **What AI feature is included?**  
    A baseline predicted performance score from historical marks; can be replaced with ML models.
