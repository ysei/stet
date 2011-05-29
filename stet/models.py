from datetime import datetime

from django.db import models
from django.conf import settings
from taggit.managers import TaggableManager

from markdown import Markdown


DATE_FMT = "%Y-%m-%d"

DRAFT = 1
LIVE = 2
HIDDEN = 3
STATUS_CHOICES = (
    (DRAFT, 'draft'),
    (LIVE, 'live'),
    (HIDDEN, 'hidden'),
)
STATUS_CHOICES_DICT = dict([(v, k) for k, v in STATUS_CHOICES])


class LiveManager(models.Manager):
    def get_query_set(self):
        return super(LiveManager, self).get_query_set().filter(status=LIVE)


class Article(models.Model):
    title = models.CharField(max_length=150)
    abstract = models.TextField(blank=True)
    body = models.TextField()
    _status = models.IntegerField(choices=STATUS_CHOICES, default=DRAFT)

    # not user-editable fields
    filename = models.CharField(max_length=150, unique=True)
    html = models.TextField()
    pub_date = models.DateTimeField(blank=True, null=True)
    last_changed = models.DateTimeField(auto_now=True)
    last_commit = models.CharField(max_length=40)

    objects = models.Manager()
    live = LiveManager()
    tags = TaggableManager()

    def __unicode__(self):
        return self.title

    def save(self, commit=None, *args, **kwargs):
        md = Markdown(extensions=settings.MARKDOWN_EXT)
        self.html = md.convert(self.body)
        self.last_commit = commit or ''
        m = md.Meta
        # process the metadata
        self.title = ' '.join(m.get('title', []))
        self.abstract = ' '.join(m.get('abstract', []))
        self.status = STATUS_CHOICES_DICT[m.get('status', ['live'])[0]]

        super(Article, self).save(*args, **kwargs)
        self.tags.set(*m.get('tags', []))

    @models.permalink
    def get_absolute_url(self):
        return ('article', [str(self.id)])

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new):
        if self._status == DRAFT and new == LIVE:
            self.pub_date = datetime.now()
        self._status = new
