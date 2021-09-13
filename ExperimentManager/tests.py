from django.test import TestCase

# Create your tests here.

def create(i):
    return [6] + [7]

a = [1,2,3]
import functools
import operator

tmp = functools.reduce(operator.iconcat, [create(i)for i in a], [])

print(tmp)