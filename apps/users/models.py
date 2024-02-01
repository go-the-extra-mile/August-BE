from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from apps.courses.models import Department, Institution


class UserManager(BaseUserManager):
    def create_user(self, email, institution, department, name, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not institution:
            raise ValueError("Users must have an institution")
        inst = Institution.objects.get(id=institution)
        if not department:
            raise ValueError("Users must have an department")
        dep = Department.objects.get(id=department)
        if dep.institution != inst:
            raise ValueError("Invalid department")
        if not name:
            raise ValueError("Users must have a name")

        user = self.model(
            email=self.normalize_email(email),
            institution=inst,
            department=dep,
            name=name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, institution, department, name, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not institution:
            raise ValueError("Users must have an institution")
        inst = Institution.objects.get(id=institution)
        if not department:
            raise ValueError("Users must have an department")
        dep = Department.objects.get(id=department)
        if dep.institution != inst:
            raise ValueError("Invalid department")
        if not name:
            raise ValueError("Users must have a name")

        user = self.create_user(
            email=email,
            password=password,
            institution=institution,
            department=department,
            name=name,
        )
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    institution = models.ForeignKey("courses.Institution", on_delete=models.DO_NOTHING)
    department = models.ForeignKey("courses.Department", on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)

    objects = UserManager()

    # log in with email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["institution", "department", "name"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True
