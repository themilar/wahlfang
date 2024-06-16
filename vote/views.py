import sys

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, views as auth_views
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
# from ratelimit.decorators import ratelimit
from django_ratelimit.decorators import ratelimit
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from vote.authentication import voter_login_required
from vote.forms import AccessCodeAuthenticationForm, VoteForm, ApplicationUploadFormUser
from vote.models import Election, Voter, Session
from vote.selectors import open_elections, upcoming_elections, published_elections, closed_elections


class LoginView(auth_views.LoginView):
    # login view settings
    # https://docs.djangoproject.com/en/3.0/topics/auth/default/#django.contrib.auth.views.LoginView
    authentication_form = AccessCodeAuthenticationForm
    template_name = 'vote/login.html'
    redirect_authenticated_user = False

    def get(self, request, *args, **kwargs):
        print(request, args)
        u = request.user
        if u.is_authenticated and isinstance(u, Voter):
            return redirect('vote:index')
        return super().get(request, *args, **kwargs)

    @method_decorator(ratelimit(key=settings.RATELIMIT_KEY, rate='10/h', method='POST'))
    def post(self, request, *args, **kwargs):
        ratelimited = getattr(request, 'limited', False)
        if ratelimited:
            return render(request, template_name='vote/ratelimited.html', status=429)
        return super().post(request, *args, **kwargs)


@ratelimit(key=settings.RATELIMIT_KEY, rate='10/h')
def code_login(request, access_code=None):
    ratelimited = getattr(request, 'limited', False)
    if ratelimited:
        return render(request, template_name='vote/ratelimited.html', status=429)

    if not access_code:
        messages.error(request, 'No access code provided.')
        return redirect('vote:code_login')

    user = authenticate(access_code=access_code)
    if not user:
        messages.error(request, 'Invalid access code.')
        return redirect('vote:code_login')

    login(request, user)

    if user.qr:
        group = "QR-Reload-" + str(user.session.pk)
        async_to_sync(get_channel_layer().group_send)(
            group,
            {'type': 'send_reload', 'link': reverse('management:add_mobile_voter', args=[user.session.pk])}
        )

    return redirect('vote:index')


@voter_login_required
def index(request):
    voter: Voter = request.user
    session = voter.session

    def list_elections(elections):
        return [
            (e, voter.can_vote(e), voter.has_applied(e))
            for e in elections
        ]

    context = {
        'title': session.title,
        'meeting_link': session.meeting_link,
        'voter': voter,
        'existing_elections': (session.elections.count() > 0),
        'open_elections': list_elections(open_elections(session)),
        'upcoming_elections': list_elections(upcoming_elections(session)),
        'published_elections': list_elections(published_elections(session)),
        'closed_elections': list_elections(closed_elections(session)),
    }

    # overview
    return render(request, template_name='vote/index.html', context=context)


@voter_login_required
def vote(request, election_id):
    voter: Voter = request.user
    try:
        election = voter.session.elections.get(pk=election_id)
    except Election.DoesNotExist:
        return HttpResponseNotFound('Election does not exists')

    can_vote = voter.can_vote(election)
    if election.max_votes_yes is not None:
        max_votes_yes = min(election.max_votes_yes,
                            election.applications.all().count())
    else:
        max_votes_yes = election.applications.all().count()

    context = {
        'title': election.title,
        'election': election,
        'voter': voter,
        'can_vote': can_vote,
        'max_votes_yes': max_votes_yes,
        'form': VoteForm(request, election=election)
    }

    if request.POST and can_vote:
        form = VoteForm(request, election=election, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('vote:index')

    return render(request, template_name='vote/vote.html', context=context)


@voter_login_required
def apply(request, election_id):
    voter = request.user

    election = get_object_or_404(voter.session.elections, pk=election_id)

    if not election.can_apply or not election.voters_self_apply:
        messages.add_message(request, messages.ERROR, 'Self applications are either not possible for this election or'
                                                      ' currently not accepted')
        return redirect('vote:index')

    application = voter.applications.filter(election__id=election_id)
    instance = None
    if application.exists():
        instance = application.first()

    if request.method == 'GET':
        form = ApplicationUploadFormUser(election, request, instance=instance)
    else:
        form = ApplicationUploadFormUser(
            election, request, data=request.POST, files=request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('vote:index')

    context = {
        'form': form,
        'election': election,
        'with_email': True,
        'with_description': True,
    }
    return render(request, template_name='vote/application.html', context=context)


@voter_login_required
def delete_own_application(request, election_id):
    voter = request.user
    election = get_object_or_404(voter.session.elections, pk=election_id)
    application = voter.applications.filter(election__id=election_id)
    if not election.can_apply:
        messages.add_message(request, messages.ERROR,
                             'Applications can currently not be deleted')
        return redirect('vote:index')
    if application.exists():
        instance = application.first()
        instance.delete()
        return redirect('vote:index')

    return HttpResponseNotFound('Application does not exist')


def help_page(request):
    return render(request, template_name='vote/help.html')


def spectator(request, uuid):
    session = get_object_or_404(Session.objects, spectator_token=uuid)

    context = {
        'title': session.title,
        'meeting_link': session.meeting_link,
        'existing_elections': (session.elections.count() > 0),
        'open_elections': open_elections(session),
        'upcoming_elections': upcoming_elections(session),
        'published_elections': published_elections(session),
        'closed_elections': closed_elections(session),
    }
    return render(request, template_name='vote/spectator.html', context=context)
