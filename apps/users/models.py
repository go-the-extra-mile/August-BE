from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from apps.courses.models import Department, Institution
from django.core.exceptions import ValidationError


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
    institution = models.ForeignKey(
        "courses.Institution", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    department = models.ForeignKey(
        "courses.Department", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    name = models.CharField(max_length=255, blank=True)
    profile_image_file = models.ImageField(upload_to="profile_images/", blank=True)
    profile_image_url = models.URLField(blank=True)

    FRESHMAN = "FR"
    SOPHOMORE = "SO"
    JUNIOR = "JR"
    SENIOR = "SR"
    GRADUATE = "GR"
    YEAR_IN_SCHOOL_CHOICES = {
        FRESHMAN: "Freshman",
        SOPHOMORE: "Sophomore",
        JUNIOR: "Junior",
        SENIOR: "Senior",
        GRADUATE: "Graduate",
    }
    year_in_school = models.CharField(
        max_length=2, choices=YEAR_IN_SCHOOL_CHOICES, default=FRESHMAN
    )

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

    def save(self, *args, **kwargs):
        # Check if the department belongs to the institution
        if self.department and self.institution:
            if self.department.institution != self.institution:
                error_dict = {
                    "department": [
                        f"Invalid department for institution {self.institution}"
                    ]
                }
                raise ValidationError(message=error_dict)
        super().save(*args, **kwargs)

    @property
    def profile_image(self):
        ret = self.profile_image_file or self.profile_image_url
        return ret or None

    @profile_image.setter
    def profile_image(self, img):
        # set profile image as provided image
        self.profile_image_file = img
        # remove profile image URL
        self.profile_image_url = str()
