from django.db import models


class RAGQA(models.Model):
    question = models.CharField(max_length=200)
    answer = models.CharField(max_length=200)
    group = models.CharField(max_length=200)
    sub_group = models.CharField(max_length=200)
    rag = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.CharField(max_length=200)
    userid = models.CharField(max_length=200)
    documents = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.question