import { CerebroDB } from '@/assets/libs/cerebro-db'

export declare const copyTextToClipboard: any

declare global {
  interface Window {
    require: any
    cep: any
    DB: CerebroDB
  }
}
