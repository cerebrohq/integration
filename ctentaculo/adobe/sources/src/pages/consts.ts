import Helpers from '@/assets/libs/helpers'
import path from 'path'
import moment from 'moment'
import { transliterate as tr } from 'transliteration'

declare global {
  interface Window {
    process: any
  }
}

enum APPS {
  PHXS = 'photoshop',
  PHSP = 'photoshop',
  AEFT = 'aftereffects',
  IDSN = 'indesign',
  ILST = 'illustrator',
  FLPR = 'animate',
  PPRO = 'premiere',
}

enum FILE_FORMATS {
  PHXS = '.psd',
  PHSP = '.psd',
  AEFT = '.aep',
  IDSN = '.indd',
  ILST = '.ai',
  FLPR = '.fla',
  PPRO = '.prproj',
}

enum HOST_ERRORS {
  UNKNOWN_HOST_ID = -1,
  CANT_CREATE_DOCUMENT = -2,
  CANT_OPEN_DOCUMENT = -3,
}

enum NET_MODE {
  NETWORK = 'NETWORK',
  LOCAL = 'LOCAL',
  REMOTE = 'REMOTE',
}

enum TYPE_MODAL {
  PUBLISH = 1,
  VERSION = 2,
}

const APP_ROOT = path.dirname(Helpers.getAppFolder())
window.APP_ROOT = APP_ROOT

const HOST_ID = Helpers.getHostID()

const LOCAL_CONFIG_PATH = path
  .join(Helpers.getAppDataFolder(), 'cerebro', 'path_config.json')
  .replace(/\\/g, '/')

const CTENTACULO_LOCATION = window.process.env['CTENTACULO_LOCATION']

const NETWORK_CONFIG_PATH = CTENTACULO_LOCATION
  ? path.join(CTENTACULO_LOCATION, 'path_config.json').replace(/\\/g, '/')
  : ''

const ROOT_DIR = Helpers.getExtensionFolder()
const TMP_DIR = Helpers.getTMPFolder()

const OS = Helpers.getOS()
const OS_BITS = Helpers.getOSBits()
Helpers.loadJSX(APPS[HOST_ID])

tr.config({
  replace: {
    ' ': '_',
  },
})

moment.locale('en', {
  calendar: {
    sameDay: '[Today at] HH:mm',
    nextDay: '[Tomorrow at] HH:mm',
    nextWeek: 'YYYY-MM-DD',
    lastDay: '[Yesterday at] HH:mm',
    lastWeek: 'YYYY-MM-DD',
    sameElse: 'YYYY-MM-DD',
  },
})

const MIRADA_PATH_MAPPING = {
  win32: 'C:\\Program Files (x86)\\Cerebro\\mirada.exe',
  win64: 'C:\\Program Files\\Cerebro\\mirada.exe',
  mac: '/Applications/Cerebro/Mirada.app',
}

export {
  APPS,
  FILE_FORMATS,
  HOST_ERRORS,
  NET_MODE,
  TYPE_MODAL,
  APP_ROOT,
  ROOT_DIR,
  TMP_DIR,
  HOST_ID,
  LOCAL_CONFIG_PATH,
  NETWORK_CONFIG_PATH,
  OS,
  OS_BITS,
  CTENTACULO_LOCATION,
  MIRADA_PATH_MAPPING,
}
