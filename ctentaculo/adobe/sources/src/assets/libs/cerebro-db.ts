import _ from 'lodash'
import Helpers from '@/assets/libs/helpers'
import path from 'path'

type NEW_ATTACHMENT_OPTIONS = {
  msgId: string
  hash: string | null
  tag: ATTACHMENT_TAG
  size: number
  filename: string
  description: string
  thumbnails: string[]
}

type NEW_MESSAGE_OPTIONS = {
  tid: string
  msg: string
  type: MESSAGE_TYPE
  hours: number
  attachments: ATTACHMENT[]
}
export type PUBLISH_OPTIONS = NEW_MESSAGE_OPTIONS

export type ATTACHMENT = {
  hash: string | null
  tag: ATTACHMENT_TAG
  size: number
  filename: string
  description: string
  thumbnails: string[]
}

enum MESSAGE_TYPE {
  DEFINITION = 0,
  REVIEW = 1,
  REPORT = 2,
  NOTE = 3,
  CLIENT_REVIEW = 4,
  RESOURCE_REPORT = 5,
  STATUS_CHANGES = 6,
}

export enum ATTACHMENT_TAG {
  FILE = 0,
  THUMB1 = 1,
  THUMB2 = 2,
  THUMB3 = 3,
  REVIEW = 4,
  LINK = 5,
}

const RPC_VERSION = '2.0'
const RPC_DEFAULT_URL = 'https://login.cerebrohq.com/dapi/rpc.php'

const RPC_HEADERS = {
  accept: 'application/json-rpc',
}

const QUERIES = {
  plain: {
    baseMtm: 'select "getBaseMTM"()',
    tasksIds: 'select uid from "taskAssigned_byUsers"(?, True)',
    statuses:
      'select *, (select name from "statusIconHashs"((\'{\' || uid || \'}\')::bigint[]) limit 1) as hash from "statusList"()',
    lastStatus:
      'select a.mtm, a.uid, a.tag, a."fullName", a.creatorid, a.ctime, a.statusid, b.uid, ((b.flags & 4) > 0) as "isWorking" from "eventQuery_08"(array(select uid from "_event_list"(?, false))) as a, "statusList"() as b where a.tag = 6 and b.uid = a.statusid order by mtm desc limit 1;',
    taskStatuses: 'select * from "statusListByTask"(?) order by order_no',
    taskAttachments:
      'select *, (select hash from "listAttachmentsTask"(?, false) as t2 where tag = 1 and t2.groupid = t1.groupid limit 1) as "thumbHash" from "listAttachmentsTask"(?, false) as t1 where tag = 0 or tag = 5 order by eventid, groupid, mtm asc',
    taskMessages:
      'select * from "eventQuery_08"(array(select uid from "_event_list"(?, false))) where "evText" <> \'\'',
    siteList: 'select * from "siteList"()',
    unidByPrj: 'select * from "getUnid_byPrj"(?)',
    universeAttribute: 'select * from "attributeUniverse"(?, ?)',
    setStatus: 'select "taskSetStatus_a"(?, ?)',
    taskStatus: 'select cc_status from "taskQuery_11"(?)',
    newMessage: 'select "eventNew"(null,?,?,?,null,?) as "messageID"',
    newAttachmentGroup: 'select "getNewAttachmentGroupID"() as "groupID"',
    newAttachment:
      'select "newAtachment_00_"(?, ?, ?, ?, ?, ?, ?) as "newAttachment"',
  },
  methods: {
    task: 'taskQuery_json',
    taskList: 'taskListTree2_json',
    taskQuery: 'taskQuery_json',
    todoTasks: 'taskMyList_json',
  },
}

export class CerebroDB {
  public host: string = ''
  public port: number = 0
  public sid: string = ''
  public queryId: number = 1
  public primaryURL: string = ''
  public secondaryURL: string = ''
  private onError: ((error: any) => void) | null = null
  public login: string = ''
  public password: string = ''
  private user: IUser | null = null

  init(host: string, port: number) {
    this.host = host
    this.port = port
  }

  async execute(
    query: string = '',
    parameters: any[] = [],
    readOnly: boolean = false,
  ) {
    const params = [query, ...parameters]
    const headers = { ...RPC_HEADERS, RpcAuth: this.sid }
    const payload = {
      id: this.queryId,
      method: 'queryMulti',
      jsonrpc: RPC_VERSION,
      params,
    }
    const connectUrl = readOnly ? this.secondaryURL : this.primaryURL
    this.queryId++
    let response = await fetch(connectUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(payload),
    })
    let data = await response.json()
    if (data.error) {
      console.error(data.error.message)
      if (typeof this.onError === 'function') {
        this.onError(data.error)
      }
      return null
    } else {
      const columns =
        data.result[0].columns && data.result[0].columns.map((o: any) => o.name)
      const rows = data.result[0].rows
      const records: any[] = _.flatMap(rows, row => _.zipObject(columns, row))
      return records
    }
  }

  async executeJson(
    method: string = '',
    parameters: any[],
    readOnly: boolean = false,
  ) {
    const params = [...parameters]
    const headers = { RpcAuth: this.sid }
    const payload = {
      id: this.queryId,
      method,
      params,
    }
    const connectUrl = readOnly ? this.secondaryURL : this.primaryURL
    this.queryId++
    let response = await fetch(connectUrl, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(payload),
    })
    let data = await response.json()
    if (data.error) {
      console.error(data.error.message)
      if (typeof this.onError === 'function') {
        this.onError(data.error)
      }
      return null
    } else {
      return data.result
    }
  }

  async connect(
    login: string,
    password: string,
    primaryUrl?: string,
    secondaryUrl?: string,
  ) {
    let directConnection = true
    if (primaryUrl == undefined) {
      directConnection = false
      primaryUrl = RPC_DEFAULT_URL
    }
    this.login = login
    this.password = password
    var payload = {
      jsonrpc: RPC_VERSION,
      method: directConnection ? 'sessionDirectStart' : 'sessionStart',
      params: [login, password, 655360],
      id: this.queryId,
    }
    var connectUrl =
      (primaryUrl.startsWith('http') ? '' : 'http') +
      primaryUrl +
      (primaryUrl.endsWith('.php') ? '' : '/rpc.php')

    this.queryId++
    const response = await fetch(connectUrl, {
      method: 'POST',
      headers: RPC_HEADERS,
      body: JSON.stringify(payload),
    })
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error.message)
    } else if (data.result.length === 0) {
      throw new Error('User not found')
    } else {
      let record = data.result[0]
      let user: IUser = record.user
      this.sid = record.token
      if (directConnection) {
        this.primaryURL = connectUrl
        this.secondaryURL = this.primaryURL
      } else {
        this.primaryURL =
          data.result[0].server.primary_server.addr_jrpc + '/rpc.php'
        this.secondaryURL = this.primaryURL
      }
      this.user = user
      return this.sid
    }
  }

  async getMTM() {
    var query = QUERIES.plain.baseMtm
    let result: any = await this.execute(query)
    if (result) {
      return result[0].getBaseMTM
    } else {
      return null
    }
  }

  async getUser(): Promise<IUser> {
    if (!this.user && this.sid) {
      this.user = await this.getDBUser()
    }
    if (this.user) {
      return this.user
    } else throw Error('User is null')
  }
  getDBUser(): IUser | PromiseLike<IUser | null> | null {
    throw new Error('Method not implemented.')
  }

  setUser(user: IUser) {
    this.user = user
  }

  async getTasksID(uid: string) {
    const query = QUERIES.plain.tasksIds
    const ids = await this.execute(query, [[uid]])
    if (Array.isArray(ids)) {
      return ids.map(o => o.uid)
    } else return null
  }

  async getTask(uid: string) {
    const [task] = await this.executeJson(QUERIES.methods.task, [[uid], '0'])
    if (task) {
      task.parent = task.parent_path || ''
      const thumbs =
        (typeof task.thumb === 'string' &&
          (task.thumb as string).split(',').filter(o => o)) ||
        []
      task.thumbHash = thumbs.length > 0 ? thumbs[thumbs.length - 1] : ''
    }
    return task
  }

  async getTodoTasks(uid?: string) {
    const tasks = await this.executeJson(QUERIES.methods.todoTasks, ['4194304'])
    if (Array.isArray(tasks)) {
      tasks.forEach(o => {
        o.parent = o.parent_path || ''
        const thumbs =
          (typeof o.thumb === 'string' &&
            (o.thumb as string).split(',').filter(o => o)) ||
          []
        o.thumbHash = thumbs.length > 0 ? thumbs[thumbs.length - 1] : ''
      })
    }
    return tasks
  }

  async getTasksIds(uid) {
    const tasks = await this.executeJson(QUERIES.methods.taskList, [
      uid ? uid : 0,
      0,
    ])
    return (Array.isArray(tasks) && tasks.map(o => o.uid)) || []
  }

  async getChildTasks(uid) {
    const ids = await this.getTasksIds(uid)
    const tasks = await this.executeJson(QUERIES.methods.taskQuery, [ids, 0])
    if (Array.isArray(tasks)) {
      tasks.forEach(o => {
        o.parent = o.parent_path || ''
        const thumbs =
          (typeof o.thumb === 'string' &&
            (o.thumb as string).split(',').filter(o => o)) ||
          []
        o.thumbHash = thumbs.length > 0 ? thumbs[thumbs.length - 1] : ''
        o.hasChild = Helpers.bitTest(o.flags, 32)
      })
    }
    return tasks
  }

  getStatuses() {
    var query = QUERIES.plain.statuses
    return this.execute(query, [])
  }

  async getTaskLastStatus(uid) {
    var query = QUERIES.plain.lastStatus
    const result = await this.execute(query, [uid])
    return result && result.length > 0 ? result[0] : null
  }

  getTaskStatuses(taskID) {
    var query = QUERIES.plain.taskStatuses
    return this.execute(query, [taskID])
  }

  getTaskAttachments(uid) {
    var query = QUERIES.plain.taskAttachments
    return this.execute(query, [uid, uid]).then(function(attachments) {
      if (attachments === null) return []
      return attachments
    })
  }

  getTaskMessages(uid: string) {
    var query = QUERIES.plain.taskMessages
    return this.execute(query, [uid])
  }

  getSitelist() {
    var query = QUERIES.plain.siteList
    return this.execute(query, [])
  }

  async getUniverseIDByProjectID(id) {
    var query = QUERIES.plain.unidByPrj
    const result = await this.execute(query, [id])
    if (result === null) return null
    else return result.length > 0 ? result[0].getUnid_byPrj : null
  }
  async getUniverseAttribute(id, num) {
    var query = QUERIES.plain.universeAttribute
    const result = await this.execute(query, [id, num])
    if (result === null) return null
    else return result.length > 0 ? result[0].attributeUniverse : null
  }
  async getUniverseAttributeByProjectID(id, num) {
    const unid = await this.getUniverseIDByProjectID(id)
    if (unid === null) {
      throw Error('Couldn`t retrieve universe attribute')
    } else {
      return await this.getUniverseAttribute(id, num)
    }
  }

  setTaskStatus(taskID, statusID) {
    if (statusID === 0) statusID = null
    var query = QUERIES.plain.setStatus
    return this.execute(query, [[taskID], statusID])
  }

  getTaskStatus(uid) {
    var query = QUERIES.plain.taskStatus
    return this.execute(query, [[uid]]).then(function(data: any) {
      return data[0].cc_status
    })
  }

  async newAttachmentGroup() {
    const [{ groupID = null } = {}] = (await this.execute(
      QUERIES.plain.newAttachmentGroup,
      [],
    )) || [{}]
    return groupID
  }

  async newAttachment({
    msgId,
    tag,
    hash,
    filename,
    size,
    description,
    thumbnails,
  }: NEW_ATTACHMENT_OPTIONS) {
    const groupId = await this.newAttachmentGroup()

    await this.execute(QUERIES.plain.newAttachment, [
      msgId,
      groupId,
      hash,
      tag,
      size,
      tag === 0 ? path.basename(filename) : filename,
      description,
    ])
    if (Array.isArray(thumbnails) && thumbnails.length > 0) {
      let tag = ATTACHMENT_TAG.THUMB1
      for (const thumb of thumbnails.slice(0, 3)) {
        await this.execute(QUERIES.plain.newAttachment, [
          msgId,
          groupId,
          thumb,
          tag,
          0,
          '',
          '',
        ])
        tag++
      }
    }
  }

  async newMessage(options: NEW_MESSAGE_OPTIONS) {
    const {
      tid,
      msg = '',
      type = MESSAGE_TYPE.NOTE,
      hours = 0,
      attachments = [],
    } = options
    const [{ messageID: msgId = null } = {}] = (await this.execute(
      QUERIES.plain.newMessage,
      [tid, msg, type, hours],
    )) || [{}]

    if (msgId && Array.isArray(attachments) && attachments.length > 0) {
      for (const o of attachments) {
        await this.newAttachment({
          msgId,
          filename: o.filename,
          hash: o.hash,
          tag: o.tag,
          size: o.size,
          description: o.description,
          thumbnails: o.thumbnails,
        })
      }
    }
  }

  publishFile(options: PUBLISH_OPTIONS) {
    return this.newMessage(options)
  }
}
