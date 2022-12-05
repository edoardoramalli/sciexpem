from django.core.management import call_command
from django.core.management.base import BaseCommand
# from django.core.management.commands.runserver import BaseRunserverCommand

# from .env import PATH_CFG_SIM, PATH_CFG_PARAM


class Command(BaseCommand):
    ''' Runs the built-in Django runserver with initial schema and fixtures
    Note: cannot use auto-reloading because that casues resetdb to be called
    twice.
    '''

    # # remove this option from the --help for this command
    # option_list = (o for o in BaseRunserverCommand.option_list if o.dest != 'use_reloader')
    # help = 'Starts a lightweight web server testing.'
    # args = '[optional port number, or ipaddr:port] appname appname'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        # parser.add_argument('--cfg-sim', action='store',
        #                     dest='path_cfg_sim',
        #                     help='Set path to simulation.yml configurations')
        # parser.add_argument('--cfg-param', action='store',
        #                     dest='path_cfg_param',
        #                     help='Set path to parameters.yml configurations')
        parser.add_argument('--config', dest='configuration')


    def handle(self, addrport='', *args, **options):

        # Set path parameters if passed
        # if options['path_cfg_sim']:
        #     PATH_CFG_SIM = options['path_cfg_sim']
        # if options['path_cfg_param']:
        #     PATH_CFG_PARAM = options['path_cfg_param']

        print(options)


        from SciExpeM.settings import settings_file_name

        settings_file_path = options.pop('configuration')

        # SettingsReader(os.path.join(BASE_DIR, 'SciExpeM', 'settingsFile'))




        # call_command('syncdb', *args, **options)
        # BUG: runserver gets called twice if --noreload is False
        # https://code.djangoproject.com/ticket/8085
        # options['use_reloader'] = False
        options.pop('skip_checks')
        call_command('runserver', addrport, *args, **options)

        return None