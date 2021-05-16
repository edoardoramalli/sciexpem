import CrowdSourcing.views as View
from random import choices

from CrowdSourcing import models

# Django import
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST


def extract_next(current):
    participants = models.Participant.objects.all().exclude(name='base')

    done = {}
    for p in participants:
        for q in p.done:
            done[int(q)] = done.get(int(q), 0) + 1

    base = [int(e) for e in models.Participant.objects.get(name='base').done]

    current = [int(e) for e in models.Participant.objects.get(name=current).done]

    remaining = set(base).difference(set(current))

    never_done = set(base).difference(set(done.keys()))

    pesi = {possible: 1 if possible not in never_done else 100 for possible in remaining}

    return choices(population=list(pesi.keys()), weights=list(pesi.values()), k=1)[0]



class getNextQuestion(View.CrowdSourcingBaseView):
    viewName = 'getNextQuestion'
    paramsType = {}
    # paramsType = {'status': str, 'exp_id': int}

    required_groups = {'POST': []}

    def view_post(self, request):
        # edo = models.Participant(name='base', done=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        # edo.save()

        # albe = models.Participant(name='alberto', done=[3, 4, 7, 10])
        #
        # timoteo = models.Participant(name='timoteo', done=[1, 4, 9, 10])
        #
        # albe.save()
        # timoteo.save()

        # current = 'alberto'
        #
        # print(extract_next(current=current))

        from sendfile import sendfile

        return sendfile(request, '/Users/edoardo/Documents/GitHub/sciexpem/Files/prop')


        return Response(status=HTTP_200_OK)
