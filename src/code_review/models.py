from ..accounts.models import User
from django.conf import settings
from django.db import models
from django.utils import dateformat
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from tagging_autocomplete.models import TagAutocompleteField
import markdown


class Snipet(models.Model):
    LANGUAGE_CHOICES = (
        ('python', u'Python'),
        ('javascript', u'JavaScript')
    )
    title = models.CharField(_(u'title'), max_length=255)
    description = models.TextField(_(u'description'), blank=True)
    language = models.CharField(_(u'language'), default='python', choices=LANGUAGE_CHOICES, max_length=100,
        help_text=_(u'Main snippet language'))
    author = models.ForeignKey(User, verbose_name=_(u'author'))
    created = models.DateTimeField(_(u'created'), auto_now_add=True)
    tags = TagAutocompleteField(verbose_name=_(u'tags'))
    rating = models.PositiveIntegerField(_(u'rating'), default=0)
    rated_by = models.ManyToManyField(User, verbose_name=_(u'rated by'), editable=False, related_name='rated_snippets')

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('code_review:details', [self.pk], {})

    def can_rate(self, user):
        if not user.is_authenticated():
            return False

        return not self.rated_by.filter(pk=user.pk).exists()


class File(models.Model):
    LANGUAGE_CHOICES = (
        ('python', u'Python'),
        ('javascript', u'JavaScript'),
        ('bash', u'Bash'),
        ('sql', u'SQL'),
        ('xml', u'XML/HTML')
    )
    name = models.CharField(_(u'file name'), max_length=1000)
    content = models.TextField(_(u'content'))
    snipet = models.ForeignKey(Snipet)
    language = models.CharField(_(u'language'), blank=True, max_length=100, choices=LANGUAGE_CHOICES)

    def __unicode__(self):
        return self.name


class Comment(models.Model):
    file = models.ForeignKey(File, verbose_name=_(u'file'))
    row = models.PositiveIntegerField(_(u'row'))
    content = models.TextField(_(u'comment'), max_length=1000)
    author = models.ForeignKey(User, verbose_name=_(u'author'), related_name='code_comments')
    created = models.DateTimeField(_(u'created'), auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return u"%s: %s..." % (self.author, self.content[:50])

    def get_content(self):
        return mark_safe(markdown.markdown(self.content, safe_mode='escape').replace('\n', '<br />'))

    def get_json(self):
        return {
            'id': self.pk,
            'row': self.row,
            'content': self.get_content(),
            'author': unicode(self.author),
            'created': dateformat.format(self.created, settings.DATETIME_FORMAT),
            'author_avatar': self.author.avatar()
        }
