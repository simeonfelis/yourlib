from django_extensions.management.jobs import BaseJob

from music.models import Playlist, PlaylistItem

# will help to migrate the change:
# PlaylistItem()
#   + playlist = ForeignKey(Playlist)
#
# Playlist()
#   - items = ManyToMany(PlaylistItme)
#
# use django_extension:
# python2 manage.py runjob music migrate_1

class Job(BaseJob):
    help = "One-time job to migrate m2m to foreign key between Playlist and PlaylistItem"

    def execute(self):
        for p in Playlist.objects.all():
            for i in p.items.all():
                i.playlist = p
                print "setting ", p, "as playlist for item ", i
                i.save()
