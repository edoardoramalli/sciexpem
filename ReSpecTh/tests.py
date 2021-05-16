from django.test import TestCase

# Create your tests here.

a = (1, 2, 3, 4)

for index in range(0, len(a)):
    if index % 2 == 0:
        a[index] += 1




