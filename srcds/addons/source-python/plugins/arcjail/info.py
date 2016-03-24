from cvars.public import PublicConVar
from plugins.info import PluginInfo


info = PluginInfo()
info.name = "ArcJail"
info.basename = 'arcjail'
info.author = 'Kirill "iPlayer" Mysnik'
info.version = '0.1'
info.variable = '{}_version'.format(info.basename)
info.convar = PublicConVar(
    info.variable, info.version, "{} version".format(info.name))

info.url = "http://arcjail.ru/"
