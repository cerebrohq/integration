<template>
  <div id="app" style="height: 100%; width: 100%">
    <PublishWindow
      :visible="PWData.visible"
      :loading="PWData.loading"
      :type="PWData.type"
      :task="PWData.task"
      :statuses="PWData.statuses"
      :statusID="PWData.statusID"
      :attachments="PWData.attachments"
      :snapshot="PWData.snapshot"
      :hours="PWData.hours"
      :text="PWData.text"
      :filename="PWData.filename"
      :filenames="PWData.filenames"
      :prefixedVersion="PWData.prefixedVersion"
      :extension="PWData.extension"
      :editable="PWData.editable"
      @status-changed="PWData = { ...PWData, statusID: $event }"
      @hours-changed="PWData = { ...PWData, hours: $event }"
      @text-changed="PWData = { ...PWData, text: $event }"
      @filename-changed="PWData = { ...PWData, filename: $event }"
      @remove-attachment="publishWindowRemoveFile"
      @add-attachment="publishWindowAddFiles"
      @close="actionClosePublishWindow"
      @ok="actionPublishFile"
    />
    <ChooseFilenameWindow
      ref="chooseFilenameWindow"
      :visible="chooseFilenameWindowData.visible"
      :filename="chooseFilenameWindowData.filename"
      :filenames="chooseFilenameWindowData.filenames"
      :editable="chooseFilenameWindowData.editable"
      @filename-changed="
        chooseFilenameWindowData = {
          ...chooseFilenameWindowData,
          filename: $event,
        }
      "
    />
    <ContextMenu ref="taskContextMenu">
      <Menu
        active-name="1"
        class="context-menu"
        width="auto"
        slot-scope="child"
      >
        <MenuItem name="1" @click.native="openTaskCerebro(child.userData)">
          Open in Cerebro
        </MenuItem>
        <MenuItem class="divider" name=""></MenuItem>
        <MenuItem name="3" @click.native="copyTaskPath(child.userData)">
          Copy Local Path to Clipboard
        </MenuItem>
        <MenuItem name="2" @click.native="openTaskExplorer(child.userData)">
          {{ osType == 'win' ? 'Open in Explorer' : 'Open in Finder' }}
        </MenuItem>
      </Menu>
    </ContextMenu>
    <ContextMenu ref="fileCM">
      <Menu
        class="context-menu"
        width="auto"
        slot-scope="child"
        @on-select="onFileCMClick($event, child.userData)"
      >
        <MenuItem
          v-for="item in filteredFileCM"
          :key="item.name"
          :name="item.name"
          :disabled="
            !item.title ||
              item.title === '' ||
              disabledFileCMItems.includes(item.name)
          "
          :class="{ divider: item.title == '' || !item.title }"
        >
          {{ item.title }}
        </MenuItem>
      </Menu>
    </ContextMenu>

    <tabs v-model="currentTab">
      <Button
        type="text"
        icon="android-refresh"
        slot="extra"
        @click="checkUpdates"
        v-tooltip.auto="{ content: 'Refresh', delay: 1000 }"
      ></Button>
      <tab-pane label="Todo list" name="todolist" class="myTasks">
        <Sidebar
          v-if="todoTab"
          :loading="todoLoading"
          :search="searchValue"
          :sort="sortValue"
          :tasks="filteredTasks"
          :selectedTask="selectedTask"
          @search-changed="searchValue = $event"
          @sort-changed="sortValue = $event"
          @task-select="onTaskSelect"
          @task-open-menu="onTaskOpenMenu"
        />
        <div class="taskContent" v-if="todoTab">
          <div
            v-if="selectedTask"
            class="taskContent-header"
            :class="{ locked: taskInWork && !ifThisUser }"
          >
            <p>
              <i
                v-if="taskInWork && !ifThisUser"
                class="ivu-icon ivu-icon-locked"
              ></i>
              {{ selectedTask.name }}
            </p>
            <breadcrumb separator=">">
              <breadcrumb-item
                v-for="(item, index) in selectedTask.parent
                  .split('/')
                  .slice(1, -1)"
                :key="index"
                >{{ item }}</breadcrumb-item
              >
            </breadcrumb>
            <row class="taskContent-info" type="flex">
              <i-col span="12">
                <row
                  type="flex"
                  v-if="selectedTask.inWork"
                  style="height: 100%"
                >
                  <i-col :xs="24" :sm="24" :md="24" :lg="12">
                    <span class="title">
                      Status:
                    </span>
                    <img
                      style="width: 16px; height: 16px"
                      v-show="
                        selectedTask.status &&
                          (selectedTask.status.imgData ||
                            selectedTask.status.thumb)
                      "
                      :src="
                        selectedTask.status.thumb
                          ? selectedTask.status.thumb
                          : selectedTask.status.imgData
                      "
                    />
                    <span v-show="selectedTask.status">
                      {{ selectedTask.status.name }}
                    </span>
                  </i-col>
                  <i-col :xs="24" :sm="24" :md="24" :lg="12">
                    <span class="inWorkUsername">{{
                      selectedTask.inWorkUsername
                    }}</span>
                    <span class="inWorkTime">{{
                      selectedTask.inWorkTime
                    }}</span>
                  </i-col>
                </row>
                <row type="flex" style="height: 100%" v-else>
                  <i-col span="24">
                    <span class="title">
                      Status:
                    </span>
                    <img
                      style="width: 16px; height: 16px"
                      v-show="
                        selectedTask.status &&
                          (selectedTask.status.imgData ||
                            selectedTask.status.thumb)
                      "
                      :src="
                        selectedTask.status.thumb
                          ? selectedTask.status.thumb
                          : selectedTask.status.imgData
                      "
                    />
                    <span v-show="selectedTask.status">
                      {{ selectedTask.status.name }}
                    </span>
                  </i-col>
                </row>
              </i-col>
              <i-col span="12"
                >Deadline:
                <span>{{ selectedTask.stop }}</span>
              </i-col>
            </row>
            <div class="action">
              <Button
                type="primary"
                shape="circle"
                icon="android-more-horizontal"
                ref="taskContextBtn"
                @click="openTaskContextBtn(selectedTask, $event)"
              ></Button>
            </div>
          </div>
          <div v-if="selectedTask" class="taskContent-main">
            <div class="taskFiles">
              <div class="attachments">
                <row class="attachments-title">
                  <i-col span="12">
                    <p class="block-title">Files</p>
                  </i-col>
                </row>
                <div
                  class="attachments-items no-files"
                  v-if="!attachments || attachments.length == 0"
                >
                  <card dis-hover :bordered="false">
                    <p>No files</p>
                  </card>
                </div>
                <div class="attachments-items" v-else>
                  <div
                    v-for="attachment in attachments"
                    class="attachments-item"
                    :key="attachment.uid"
                  >
                    <row
                      class="attachment-filename"
                      :class="{
                        selected: selectedAttachmentID
                          ? attachment.uid ==
                              selectedAttachmentID.attachment.uid &&
                            !selectedAttachmentID.localFile
                          : false,
                      }"
                      @contextmenu.native.prevent="
                        openFileCM(attachment, $event)
                      "
                      @click.native="actionSelectAttachment(attachment, false)"
                    >
                      <i-col
                        span="14"
                        v-tooltip.auto="{
                          content: attachment.filename,
                          delay: 1000,
                        }"
                        :style="{
                          paddingLeft: attachment.isChild ? '10px' : 0,
                        }"
                      >
                        {{ attachment.filename }}
                      </i-col>
                      <i-col
                        span="7"
                        style="text-align: center"
                        v-tooltip.auto="{
                          content: attachment.added,
                          delay: 1000,
                        }"
                      >
                        {{ attachment.added }}
                      </i-col>
                    </row>
                  </div>
                </div>
                <hr />
                <div class="files-buttons">
                  <Button
                    :disabled="taskInWork && !ifThisUser"
                    style="margin-left: 11px"
                    type="primary"
                    shape="circle"
                    @click="onStartWorkBtnClick"
                  >
                    {{ workingBtnLabel }}
                  </Button>
                  <Button
                    v-tooltip.auto="'New file'"
                    :disabled="taskInWork && !ifThisUser"
                    type="primary"
                    shape="circle"
                    icon="ios-plus-empty"
                    @click="onNewFileBtnClick"
                  />
                </div>
              </div>
              <div class="preview" :style="attachmentPreview"></div>
            </div>
            <div class="taskDefinition">
              <p class="block-title">Forum</p>
              <div
                class="def-text"
                v-if="selectedTask.messages && selectedTask.messages.length > 0"
              >
                <div
                  class="container"
                  v-for="message in selectedTask.messages"
                  :key="message.uid"
                  :class="{ darker: message.authorID == usid }"
                >
                  <p
                    class="message-type"
                    :class="{
                      definition: message.typeID == 0,
                      review: message.typeID == 1,
                      report: message.typeID == 2,
                      note: message.typeID == 3,
                      'client-review': message.typeID == 4,
                      'resource-report': message.typeID == 5,
                    }"
                  >
                    {{ message.type }}
                  </p>
                  <p class="author">{{ message.author }}</p>
                  <span class="time-right">{{ message.creationTime }}</span>
                  <p class="message" v-html="message.text" />
                </div>
              </div>
              <div
                v-else
                style="padding: 16px; font-size: 13px; color: #a0a0a0; text-align: center"
              >
                <p>No messages</p>
              </div>
            </div>
          </div>
          <div v-if="selectedTask" class="taskContent-footer">
            <div class="btnGroup">
              <Button
                :disabled="
                  Object.keys(openedFiles).length == 0 &&
                    (!taskInWork || (taskInWork && !ifThisUser))
                "
                @click="openPublishWindow(TYPE_MODAL.VERSION)"
                style="margin-right: 10px"
                type="primary"
                shape="circle"
                >Save as New Version</Button
              >
              <Button
                :disabled="
                  Object.keys(openedFiles).length == 0 &&
                    (!taskInWork || (taskInWork && !ifThisUser))
                "
                @click="openPublishWindow(TYPE_MODAL.PUBLISH)"
                style="margin-right: 10px"
                type="primary"
                shape="circle"
              >
                Publish</Button
              >
            </div>
          </div>
        </div>
      </tab-pane>
      <tab-pane label="Browser" name="browser" class="browser">
        <Sidebar
          v-if="browserTab"
          :loading="browserLoading"
          :search="searchValue"
          :sort="sortValue"
          :tasks="filteredTasks"
          :selectedTask="selectedTask"
          :breadcrumbs="browserHistory"
          variant="browser"
          @search-changed="searchValue = $event"
          @sort-changed="sortValue = $event"
          @task-select="onTaskSelect"
          @task-open-menu="onTaskOpenMenu"
          @task-parent-open="browserBack"
          @task-child-open="openChildrenTask"
        />
        <div class="taskContent" v-if="browserTab">
          <div
            v-if="selectedTask"
            class="taskContent-header"
            :class="{ locked: taskInWork && !ifThisUser }"
          >
            <p>
              <i
                v-if="taskInWork && !ifThisUser"
                class="ivu-icon ivu-icon-locked"
              ></i>
              {{ selectedTask.name }}
            </p>
            <breadcrumb separator=">">
              <breadcrumb-item
                v-for="(item, index) in selectedTask.parent
                  .split('/')
                  .slice(1, -1)"
                :key="index"
                >{{ item }}</breadcrumb-item
              >
            </breadcrumb>
            <row class="taskContent-info" type="flex">
              <i-col span="12">
                <row
                  type="flex"
                  v-if="selectedTask.inWork"
                  style="height: 100%"
                >
                  <i-col :xs="24" :sm="24" :md="24" :lg="12">
                    <span class="title">
                      Status:
                    </span>
                    <img
                      style="width: 16px; height: 16px"
                      v-show="
                        selectedTask.status &&
                          (selectedTask.status.imgData ||
                            selectedTask.status.thumb)
                      "
                      :src="
                        selectedTask.status.thumb
                          ? selectedTask.status.thumb
                          : selectedTask.status.imgData
                      "
                    />
                    <span v-show="selectedTask.status">
                      {{ selectedTask.status.name }}
                    </span>
                  </i-col>
                  <i-col :xs="24" :sm="24" :md="24" :lg="12">
                    <span class="inWorkUsername">{{
                      selectedTask.inWorkUsername
                    }}</span>
                    <span class="inWorkTime">{{
                      selectedTask.inWorkTime
                    }}</span>
                  </i-col>
                </row>
                <row type="flex" style="height: 100%" v-else>
                  <i-col span="24">
                    <span class="title">
                      Status:
                    </span>
                    <img
                      style="width: 16px; height: 16px"
                      v-show="
                        selectedTask.status &&
                          (selectedTask.status.imgData ||
                            selectedTask.status.thumb)
                      "
                      :src="
                        selectedTask.status.thumb
                          ? selectedTask.status.thumb
                          : selectedTask.status.imgData
                      "
                    />
                    <span v-show="selectedTask.status">
                      {{ selectedTask.status.name }}
                    </span>
                  </i-col>
                </row>
              </i-col>
              <i-col span="12"
                >Deadline:
                <span>{{ selectedTask.stop }}</span>
              </i-col>
            </row>
            <div class="action">
              <Button
                type="primary"
                shape="circle"
                icon="android-more-horizontal"
                ref="taskContextBtn"
                @click="openTaskContextBtn(selectedTask, $event)"
              ></Button>
            </div>
          </div>
          <div v-if="selectedTask" class="taskContent-main">
            <div class="taskFiles">
              <div class="attachments">
                <row class="attachments-title">
                  <i-col span="12">
                    <p class="block-title">Files</p>
                  </i-col>
                </row>
                <div
                  class="attachments-items no-files"
                  v-if="
                    !selectedTask.attachments ||
                      selectedTask.attachments.length == 0
                  "
                >
                  <card dis-hover :bordered="false">
                    <p>No files</p>
                  </card>
                </div>
                <div class="attachments-items" v-else>
                  <div
                    v-for="attachment in attachments"
                    class="attachments-item"
                    :key="attachment.uid"
                  >
                    <row
                      class="attachment-filename"
                      :class="{
                        selected: selectedAttachmentID
                          ? attachment.uid ==
                              selectedAttachmentID.attachment.uid &&
                            !selectedAttachmentID.localFile
                          : false,
                      }"
                      @contextmenu.native.prevent="
                        openFileCM(attachment, $event)
                      "
                      @click.native="actionSelectAttachment(attachment, false)"
                    >
                      <i-col
                        span="14"
                        v-tooltip.auto="{
                          content: attachment.filename,
                          delay: 1000,
                        }"
                        :style="{
                          paddingLeft: attachment.isChild ? '10px' : 0,
                        }"
                      >
                        {{ attachment.filename }}
                      </i-col>
                      <i-col
                        span="7"
                        style="text-align: center"
                        v-tooltip.auto="{
                          content: attachment.added,
                          delay: 1000,
                        }"
                      >
                        {{ attachment.added }}
                      </i-col>
                    </row>
                  </div>
                </div>
                <hr />
                <div class="files-buttons">
                  <Button
                    :disabled="taskInWork && !ifThisUser"
                    style="margin-left: 11px"
                    type="primary"
                    shape="circle"
                    @click="onStartWorkBtnClick"
                  >
                    {{ workingBtnLabel }}
                  </Button>
                  <Button
                    v-tooltip.auto="'New file'"
                    :disabled="taskInWork && !ifThisUser"
                    type="primary"
                    shape="circle"
                    icon="ios-plus-empty"
                    @click="onNewFileBtnClick"
                  />
                </div>
              </div>
              <div class="preview" :style="attachmentPreview"></div>
            </div>
            <div class="taskDefinition">
              <p class="block-title">Forum</p>
              <div
                class="def-text"
                v-if="selectedTask.messages && selectedTask.messages.length > 0"
              >
                <div
                  class="container"
                  v-for="message in selectedTask.messages"
                  :key="message.uid"
                  :class="{ darker: message.authorID == usid }"
                >
                  <p
                    class="message-type"
                    :class="{
                      definition: message.typeID == 0,
                      review: message.typeID == 1,
                      report: message.typeID == 2,
                      note: message.typeID == 3,
                      'client-review': message.typeID == 4,
                      'resource-report': message.typeID == 5,
                    }"
                  >
                    {{ message.type }}
                  </p>
                  <p class="author">{{ message.author }}</p>
                  <span class="time-right">{{ message.creationTime }}</span>
                  <p class="message" v-html="message.text" />
                </div>
              </div>
              <div
                v-else
                style="padding: 16px; font-size: 13px; color: #a0a0a0; text-align: center"
              >
                <p>No messages</p>
              </div>
            </div>
          </div>
          <div v-if="selectedTask" class="taskContent-footer">
            <div class="btnGroup">
              <Button
                :disabled="
                  Object.keys(openedFiles).length == 0 &&
                    (!taskInWork || (taskInWork && !ifThisUser))
                "
                @click="openPublishWindow(TYPE_MODAL.VERSION)"
                style="margin-right: 10px"
                type="primary"
                shape="circle"
                >Save as New Version</Button
              >
              <Button
                :disabled="
                  netMode == NET_MODE.REMOTE ||
                    (Object.keys(openedFiles).length == 0 &&
                      (!taskInWork || (taskInWork && !ifThisUser)))
                "
                @click="openPublishWindow(TYPE_MODAL.PUBLISH)"
                style="margin-right: 10px"
                type="primary"
                shape="circle"
              >
                Publish</Button
              >
            </div>
          </div>
        </div>
      </tab-pane>
    </tabs>
    <spin size="large" fix v-if="appLoading"></spin>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue, Watch } from 'vue-property-decorator'
import path from 'path'
import fs from 'fs-extra'
import Helpers from '@/assets/libs/helpers'
import CerebroConfig from '@/assets/libs/cerebro-config'
import ConfigPool from '@/assets/libs/config-pool'
import _ from 'lodash'
import { CerebroDB, ATTACHMENT_TAG } from '@/assets/libs/cerebro-db'
import { parseString as xmlParse } from 'xml2js'
import {
  TYPE_MODAL,
  HOST_ID,
  APPS,
  NET_MODE,
  OS,
  FILE_FORMATS,
} from '@/pages/consts'
import Datastore from 'nedb'
import CargadorAPI from '@/assets/libs/cargador-rpc'
import XPMParser from '@/assets/libs/libxpm'
import moment from 'moment'
import ContextMenu from 'vue-lil-context-menu/index.vue'
import PublishWindow from '@/components/PublishWindow.vue'
import ChooseFilenameWindow from '@/components/ChooseFilenameWindow.vue'
import Sidebar from '@/components/Sidebar.vue'
import HostApp from '@/assets/libs/host-app'
import { PUBLISH_OPTIONS, ATTACHMENT } from '@/assets/libs/cerebro-db'

declare const DB: CerebroDB
const configPool = new ConfigPool()
var DEBUG = true
const Log = (...a) => {
  try {
    if (DEBUG) console.log('Tentaculo: ', ...a)
  } catch (e) {
    console.error(e)
  }
}
const LogError = (...a) => {
  try {
    if (DEBUG) console.error('Tentaculo error: ', ...a)
  } catch (e) {
    console.error(e)
  }
}

interface IPublishWindowAttachment {
  link: boolean
  filename: string
}

interface IPublishWindowData {
  loading: boolean
  visible: boolean
  type: TYPE_MODAL
  task: any
  snapshot: string
  statuses: any[]
  statusID: number
  filename: string
  filenames: string | string[]
  extension: string
  prefixedVersion: string
  editable: boolean
  text: string
  hours: number
  attachments: IPublishWindowAttachment[]
}

interface ChooseFilenameDialog {
  visible?: boolean
  editable: boolean
  filename?: string
  filenames: string[]
}

@Component({
  components: { ContextMenu, PublishWindow, ChooseFilenameWindow, Sidebar },
})
export default class App extends Vue {
  TYPE_MODAL = TYPE_MODAL
  NET_MODE = NET_MODE
  configs: any = {}
  chooseFilenameWindowData: ChooseFilenameDialog = {
    visible: false,
    editable: false,
    filename: '',
    filenames: [],
  }
  fileCMItems: any[] = []
  disabledFileCMItems: any[] = []
  selectedTask: any = null
  IMG_PLACEHOLDER: string = require('@/assets/image-placeholder.png')
  searchValue: string = ''
  todoLoading: boolean = false
  browserLoading: boolean = false
  browserTaskID: string | null = null
  sortValue: string = 'name'
  browserHistory: any[] = []
  currentTab: string = 'todolist'
  versionIsVisible: boolean = true
  tempDir: string = Helpers.getTMPFolder()
  thumbsDir: string = ''
  openedFiles: any = new CerebroConfig(
    path.join(Helpers.getAppDataFolder(), 'cerebro', 'taskfile_config.json'),
    {},
  )
  osType: string = OS
  db: any = new Datastore({
    filename: path.join(Helpers.getAppDataFolder(), 'cerebro', 'files.db'),
    autoload: true,
  })
  appLoading: boolean = true
  sid: any = null
  usid: any = null
  username: any = null
  currentLanguage: any = Helpers.getHostEnvironment().appUILocale
  httpHosts: any = []
  rpcHosts: any = []
  lastMTM: any = Date.now()
  statuses: any = []
  selectedTaskID: any = null
  selectedAttachmentID: any = null
  tasks: any = []
  browserTasks: any = []
  publishWindow: any = false
  saveVersionWindow: any = false
  reportWindow: any = false
  openRPublishWindow: boolean = false
  openedFile: any = null
  PWData: IPublishWindowData = {
    visible: false,
    type: TYPE_MODAL.VERSION,
    task: null,
    snapshot: '',
    statuses: [],
    filename: '',
    filenames: [],
    extension: '',
    prefixedVersion: '',
    editable: false,
    text: '',
    hours: 5,
    statusID: 0,
    attachments: [],
    loading: false,
  }
  openReportWindow: boolean = false
  downloadFolder: string = ''
  openSaveVersionWindow: boolean = false

  created() {
    //DB.onerror = this.onDBError

    Log('app', APPS[HOST_ID])
    this.fileCMItems = [
      { name: 'edit_file', title: 'Edit' },
      { name: 'open_file', title: 'Open' },
      { name: 'divider1' },
      { name: 'download_file', title: 'Download' },
      { name: 'download_edit_file', title: 'Download and edit' },
      {
        name: 'download_open_file',
        title: 'Download and open',
      },
      { name: 'divider2' },
      { name: 'open_fs_file', title: 'Open in file system' },
      { name: 'copy_path_file', title: 'Copy local path' },
    ]

    setInterval(() => {
      Helpers.dispatchEvent('onMainWindowOpened')
    }, 500)
  }

  mounted() {
    Helpers.addEventListener('responseData', this.init)
    Helpers.addEventListener('closeMainWindow', this.closeWindow)
    Helpers.addEventListener(
      'openPublishModal',
      this.openPublishWindow.bind(this, TYPE_MODAL.PUBLISH),
    )
    Helpers.addEventListener(
      'openSaveVersionModal',
      this.openPublishWindow.bind(this, TYPE_MODAL.VERSION),
    )
    Helpers.dispatchEvent('requestData')
  }

  beforeDestroy() {
    Helpers.removeEventListener('responseData', this.init)
    Helpers.removeEventListener('closeMainWindow', this.closeWindow)
    Helpers.removeEventListener(
      'openPublishModal',
      this.openPublishWindow.bind(this, TYPE_MODAL.PUBLISH),
    )
    Helpers.removeEventListener(
      'openSaveVersionModal',
      this.openPublishWindow.bind(this, TYPE_MODAL.VERSION),
    )
  }

  onFileCMClick(name, file) {
    const menu = <any>this.$refs['fileCM']
    if (menu) menu.close()
    switch (name) {
      case 'edit_file':
        this.actionEditFile(file)
        break
      case 'open_file':
        this.openFileJust(file)
        break
      case 'download_file':
        this.actionDownloadFile(file)
        break
      case 'download_edit_file':
        this.actionDownloadEditFile(file)
        break
      case 'download_open_file':
        this.actionDownloadOpenFile(file)
        break
      case 'open_fs_file':
        this.openFileExplorer(file)
        break
      case 'copy_path_file':
        this.copyFilePath(file)
        break
      default:
        LogError(`Unknown context item '${name}'`)
        break
    }
  }

  get todoTab() {
    return this.currentTab === 'todolist'
  }

  get browserTab() {
    return this.currentTab === 'browser'
  }

  get attachments() {
    const task = this.selectedTask
    if (!task) return []
    if (!task.attachments) return []
    const config = configPool.config(task.prj_id)
    if (!config) return []
    const prefix = config.getVersionPrefix(task)
    let attachments = [...task.attachments]
    let publishPath = ''
    if (config.getNetmode() !== NET_MODE.REMOTE) {
      try {
        publishPath = config.getFullPublishPath(task)
        if (!publishPath) return attachments
        const _attachments = _.groupBy(attachments, o =>
          config.getFilename(prefix, path.basename(o.originalfilename)),
        )
        for (const [publishFilename, versions] of Object.entries(
          _attachments,
        )) {
          const publishFullpath = Helpers.pathJoin(publishPath, publishFilename)
          if (fs.existsSync(publishFullpath)) {
            versions.forEach(o => (o.isChild = true))
            attachments = [
              ...attachments,
              {
                uid: path.basename(publishFullpath) + '_publish',
                originalfilename: publishFullpath,
                filename: path.basename(publishFullpath),
                added: '',
              },
            ]
          }
        }
      } catch (error) {
        LogError(error)
      }
    }
    attachments = _.orderBy(
      attachments,
      [
        config.sortFilesByName.bind(null, prefix),
        config.sortFilesByVersions.bind(null, prefix, 'desc'),
      ],
      ['asc', 'desc'],
    )
    return attachments
  }

  get netMode() {
    const task = this.selectedTask
    if (!task) return NET_MODE.REMOTE
    const config = configPool.config(task.prj_id)
    if (!config) return NET_MODE.REMOTE
    return config.getNetmode()
  }

  get filteredTasks() {
    let result = this.currentTab == 'todolist' ? this.tasks : this.browserTasks
    let tasks = [...result]
    tasks = _.chain(tasks)
      .filter(o => (o.parent + o.name).indexOf(this.searchValue) != -1)
      .filter(o => {
        if (this.currentTab !== 'todolist') return true
        const config = configPool.config(o.prj_id)
        let statusesList = config ? config.getStatusFilter() : []
        if (Array.isArray(statusesList) && statusesList.length > 0) {
          statusesList = statusesList.map(o => o.trim())
          if (o.status && o.status.name) {
            return statusesList.includes(o.status.name.trim())
          } else return false
        } else {
          return o.status && !Helpers.bitTest(o.status.flags, 3)
        }
      })
      .value()
    switch (this.sortValue) {
      case 'name':
        tasks = _.sortBy(tasks, [o => o.name.toLowerCase(), 'created'])
        break
      case 'status':
        tasks = _.sortBy(tasks, [
          o =>
            o.status && o.status.order_no && !isNaN(Number(o.status.order_no))
              ? Number(o.status.order_no)
              : 0,
          o => o.name.toLowerCase(),
        ])
        break
      case 'activity':
        tasks = _.sortBy(tasks, ['activity', o => o.name.toLowerCase()])
        break
      case 'deadline':
        tasks = _.sortBy(tasks, ['deadline', o => o.name.toLowerCase()])
        break
      case 'order':
        tasks = _.sortBy(tasks, ['seq_order', o => o.name.toLowerCase()])
        break
      case 'parent':
        tasks = _.sortBy(tasks, [
          o => {
            const parentParts = o.parent.split('/').filter(o => o)
            return parentParts[0]
          },
          o => o.name.toLowerCase(),
        ])
        break
      default:
        break
    }
    return tasks
  }

  get attachmentPreview() {
    if (!this.getSelectedAttachment)
      return {
        'background-image': `url(${this.IMG_PLACEHOLDER})`,
        'background-size': '58px 36px',
      }
    if (this.getSelectedAttachment.thumbPath) {
      this.getSelectedAttachment.thumbPath = Helpers.toCorrectPath(
        this.getSelectedAttachment.thumbPath,
      )
      return {
        'background-image': `url(${this.getSelectedAttachment.thumbPath})`,
      }
    }
    return {
      'background-image': `url(${this.IMG_PLACEHOLDER})`,
      'background-size': '58px 36px',
    }
  }

  get getSelectedTask() {
    return _.find(_.concat(this.tasks, this.browserTasks), [
      'uid',
      this.selectedTaskID,
    ])
  }
  get getSelectedAttachment() {
    if (
      !this.selectedTask ||
      !this.selectedAttachmentID ||
      !this.selectedAttachmentID.attachment
    )
      return null
    return this.selectedAttachmentID.attachment
  }
  get taskInWork() {
    if (!this.selectedTask) return false
    return this.selectedTask.inWork
  }
  get ifThisUser() {
    if (!this.selectedTask) return false
    return +this.usid === +this.selectedTask.inWorkCreatorID
  }
  get isRemoteMode() {
    return this.netMode == NET_MODE.REMOTE
  }

  get workingBtnLabel() {
    return this.getSelectedAttachment
      ? 'Start working on this file'
      : 'Start working on this task'
  }

  async init(event) {
    try {
      const {
        downloadFolder,
        host,
        login,
        openPublishModal,
        openSaveVersionModal,
        openReportModal,
        password,
        port,
        primaryURL,
        queryId,
        secondaryURL,
        sid,
        username,
        usid,
        openedFile,
        taskID,
      } = event.data
      if (openPublishModal === true) {
        this.openRPublishWindow = true
        this.openedFile = openedFile
        this.selectedTaskID = taskID
      } else if (openReportModal === true) {
        this.openReportWindow = true
      } else if (openSaveVersionModal === true) {
        this.openSaveVersionWindow = true
      }
      this.sid = sid
      this.usid = usid
      this.username = username
      this.downloadFolder = downloadFolder
      if (fs.existsSync(this.downloadFolder)) {
        this.thumbsDir = Helpers.pathJoin(this.downloadFolder, '.thumbs')
      } else {
        this.thumbsDir = Helpers.pathJoin(this.tempDir, '.thumbs')
      }
      Helpers.makePath(this.thumbsDir)
      Helpers.setWindowTitle(`Todo list : ${this.username}`)
      DB.init(event.data.host, event.data.port)
      DB.sid = this.sid
      DB.queryId = queryId
      DB.primaryURL = primaryURL
      DB.secondaryURL = secondaryURL
      DB.login = login
      DB.password = password
      this.db.loadDatabase()
      var siteList = (await DB.getSitelist()) || []
      siteList.forEach(site => {
        if (site.localaddr) {
          site.localaddr = site.localaddr.split(':')
          if (site.localaddr && site.localaddr[0])
            this.rpcHosts.push({
              local: true,
              host: site.localaddr[0],
              port: 4040,
              name: site.name,
              nativeport: site.nativeport,
            })
        }
        this.httpHosts.push({
          local: false,
          host: site.dns_name,
          port: site.webport ? site.webport : 4080,
          name: site.name,
          nativeport: site.nativeport,
        })
      })
      await CargadorAPI.connect(_.concat(this.rpcHosts, this.httpHosts))
      var statuses = await DB.getStatuses()
      _.each(statuses, async status => {
        if (status.iconXpm) {
          status.imgData = XPMParser.xpmToData(status.iconXpm)
        }
        if (status.hash) {
          status.hash64 = Helpers.hash16to64(status.hash)
          var thumbDir = path.join(this.thumbsDir, status.hash + '.svg')
          if (fs.existsSync(thumbDir)) {
            status.thumb = thumbDir
          } else {
            await Helpers.downloadFile(
              status.hash,
              thumbDir,
              'icons',
              this.httpHosts,
            )
            status.thumb = thumbDir
          }
        }
      })
      this.statuses = statuses
      this.checkUpdates()
      setInterval(this.checkUpdates, 60000)
      this.appLoading = false
      const splashEl = document.getElementById('splash')
      if (splashEl) splashEl.classList.add('hidden')
      Log('Download folder', this.downloadFolder)
      Log('Thumbs folder', this.thumbsDir)
      Log('SID', this.sid)
      Log('USID', this.usid)
      Log('HTTP hosts', this.httpHosts)
      Log('RPC hosts', this.rpcHosts)
    } catch (e) {
      console.error(e)
    }
  }

  get filteredFileCM() {
    const items = [...this.fileCMItems]
    const isRemoteMode = this.netMode === NET_MODE.REMOTE
    const remoteItems = [
      'divider1',
      'download_file',
      'download_edit_file',
      'download_open_file',
    ]
    return items.filter(o => {
      return (
        (isRemoteMode && remoteItems.includes(o.name)) ||
        !remoteItems.includes(o.name)
      )
    })
  }

  closeWindow() {
    Helpers.closeExtension()
  }
  onDBError(error) {
    Helpers.dispatchEvent('mainWindowDBError', {
      code: error.code,
      message: error.message,
    })
    Helpers.closeExtension()
  }

  publishWindowAddFiles(link) {
    const files = window.cep.fs.showOpenDialog(true)
    this.PWData = {
      ...this.PWData,
      attachments: [
        ...this.PWData.attachments,
        ...files.data.map(filename => ({
          link,
          filename,
        })),
      ],
    }
  }

  publishWindowRemoveFile(index) {
    const attachments = [...this.PWData.attachments]
    attachments.splice(index, 1)
    this.PWData = {
      ...this.PWData,
      attachments,
    }
  }
  openTaskCerebro(task) {
    ;(<any>this.$refs['taskContextMenu']).close()
    var url = `https://cerebrohq.com/cr_astro.php?protocol=cerebro&tid=${task.uid}&url=${task.parent}${task.name}`
    Helpers.openUrl(url)
  }
  openTaskExplorer(task) {
    try {
      ;(<any>this.$refs['taskContextMenu']).close()
      const config = configPool.config(task.prj_id)
      if (!config) throw Error('Config not loaded. Please wait')
      const fullPath = config.getTaskPath(task)
      if (!fullPath) throw Error('Task not configured')
      if (!fs.existsSync(fullPath))
        throw Error(`Folder '${fullPath}' not exists`)
      Helpers.openFS(fullPath)
    } catch (error) {
      this.$Message.error(error.message)
      LogError(error)
    }
  }
  copyTaskPath(task) {
    try {
      ;(<any>this.$refs['taskContextMenu']).close()
      const config = configPool.config(task.prj_id)
      if (!config) throw Error('Config not loaded. Please wait')
      const fullPath = config.getTaskPath(task)
      if (!fullPath) throw Error('Task not configured')
      if (!fs.existsSync(fullPath))
        throw Error(`Folder '${fullPath}' not exists`)
      Helpers.copyText(fullPath)
      this.$Message.info('Local path copied!')
    } catch (error) {
      this.$Message.error(error.message)
      LogError(error)
    }
  }
  async openFileExplorer(attachment) {
    try {
      if (!attachment) throw Error('File not selected')
      if (!this.selectedTask) throw Error('Task not selected')
      const task = this.selectedTask
      const config = configPool.config(task.prj_id)
      if (!config) throw Error('Config not loaded. Please wait')
      if (this.isRemoteMode && !attachment.downloaded)
        throw Error('File not downloaded')
      let fullPath = ''
      if (this.isRemoteMode) {
        const file = await Helpers.findFile(this.db, {
          hash: attachment.hash,
          path: attachment.filepath,
          originalname: attachment.originalfilename,
        })
        if (!file) throw Error('File not found')
        fullPath = Helpers.pathJoin(file.path, file.displayname)
      } else {
        fullPath = attachment.originalfilename
      }
      if (!fs.existsSync(fullPath)) throw Error('File not exists')
      Helpers.openFS(fullPath, true)
    } catch (error) {
      this.$Message.error(error.message)
      LogError(error)
    }
  }
  async copyFilePath(attachment) {
    try {
      if (!attachment) throw Error('File not selected')
      if (!this.selectedTask) throw Error('Task not selected')
      const task = this.selectedTask
      const config = configPool.config(task.prj_id)
      if (!config) throw Error('Config not loaded. Please wait')
      if (this.isRemoteMode && !attachment.downloaded)
        throw Error('File not downloaded')
      let fullPath = ''
      if (this.isRemoteMode) {
        const file = await Helpers.findFile(this.db, {
          hash: attachment.hash,
          path: attachment.filepath,
          originalname: attachment.originalfilename,
        })
        if (!file) throw Error('File not found')
        fullPath = Helpers.pathJoin(file.path, file.displayname)
      } else {
        fullPath = attachment.originalfilename
      }
      if (!fs.existsSync(fullPath)) throw Error('File not exists')
      Helpers.copyText(fullPath)
      this.$Message.info('File path copied!')
    } catch (error) {
      this.$Message.error(error.message)
      LogError(error)
    }
  }
  async openFileCM(attachment, event) {
    attachment.downloaded = true
    if (this.isRemoteMode) {
      const count = await Helpers.countFile(this.db, {
        hash: attachment.hash,
        path: attachment.filepath,
        originalname: attachment.originalfilename,
      })
      if (count == 0) attachment.downloaded = false
    }
    const fileDownloaded = !!attachment.downloaded || !!attachment.downloading
    this.disabledFileCMItems = fileDownloaded
      ? ['download_file', 'download_open_file', 'download_edit_file']
      : ['edit_file', 'open_file', 'open_fs_file', 'copy_path_file']
    const contextMenu = <any>this.$refs['fileCM']
    contextMenu.open(event, attachment)
  }
  openTaskContextBtn(task, event) {
    const menu = <any>this.$refs['taskContextMenu']
    const menuEl = menu.$el
    if (menuEl) {
      let menuWidth = 0
      menuEl.style.display = ''
      menuWidth = menuEl.offsetWidth
      menuEl.style.display = 'none'
      menu.open(
        {
          clientX: event.clientX - menuWidth,
          clientY: event.clientY,
        },
        task,
      )
    }
  }
  onTaskOpenMenu(event, task) {
    ;(<any>this.$refs['taskContextMenu']).open(event, task)
  }
  async actionEditFile(attachment) {
    try {
      await this.openFile(attachment)
      this.$Message.success('File is opened!')
    } catch (error) {
      this.$Message.error(error.message)
    }
  }
  async openFileJust(attachment) {
    try {
      let filePath = ''
      if (!this.isRemoteMode) {
        filePath = Helpers.pathNormalize(attachment.originalfilename)
      } else {
        const file = await Helpers.findFile(this.db, {
          hash: attachment.hash,
          path: attachment.filepath,
          originalname: attachment.originalfilename,
        })
        filePath = Helpers.pathJoin(file.path, file.displayname)
      }
      await HostApp.openFile(filePath)
      this.$Message.success('File is opened!')
    } catch (error) {
      this.$Message.error('Can`t open file')
      LogError(error)
    }
  }
  async actionDownloadFile(attachment) {
    if (attachment.downloaded || attachment.downloading) return
    try {
      await this.downloadFile(attachment)
      this.$Message.success('File is downloaded!')
    } catch (error) {
      this.$Message.error(error.message)
    }
  }
  async actionDownloadEditFile(attachment) {
    if (attachment.downloaded || attachment.downloading) return
    try {
      await this.downloadFile(attachment)
      await this.openFile(attachment)
    } catch (error) {
      this.$Message.error(error.message)
    }
  }
  async actionDownloadOpenFile(attachment) {
    if (attachment.downloaded || attachment.downloading) return
    try {
      await this.downloadFile(attachment)
      const attach: any = await this.findDBFile({
        hash: attachment.hash,
        path: attachment.filepath,
        originalname: attachment.originalfilename,
      })
      var filename = Helpers.pathJoin(attach.filepath, attach.displayname)
      await HostApp.openFile(filename)
      this.$Message.success('File is opened!')
    } catch (error) {
      this.$Message.error(error.message)
      LogError(error)
    }
  }
  async onStartWorkBtnClick() {
    if (!this.selectedTask) return
    try {
      await this.takeTaskToWork()
      if (this.getSelectedAttachment) {
        if (
          this.netMode === NET_MODE.REMOTE &&
          !this.getSelectedAttachment.downloaded
        ) {
          await this.downloadFile(this.getSelectedAttachment)
        }
        this.openFile(this.getSelectedAttachment)
      } else {
        await this.createFile()
      }
    } catch (error) {
      console.error(error)
      this.$Message.error(error.message)
    }
  }

  async onNewFileBtnClick() {
    if (!this.selectedTask) return
    try {
      await this.takeTaskToWork()
      await this.createFile()
    } catch (error) {
      LogError(error)
      this.$Message.error(error.message)
    }
  }
  async onTaskSelect(_task) {
    var task = _.find(_.concat(this.tasks, this.browserTasks), [
      'uid',
      _task.uid,
    ])
    if (!task) throw Error('Can`t find task')
    if (task.statuses === null) {
      const statuses = await DB.getTaskStatuses(task.uid)
      if (statuses === null) task.statuses = []
      else task.statuses = statuses
    }
    // if (task.messages === null) {
    //   task.messages = []
    //   const messages = (await DB.getTaskMessages(task.uid)) || []
    //   messages.forEach(o => {
    //     var type = ''
    //     switch (+o.tag) {
    //       case 0:
    //         type = 'Definition'
    //         break
    //       case 1:
    //         type = 'Review'
    //         break
    //       case 2:
    //         type = 'Report'
    //         break
    //       case 3:
    //         type = 'Note'
    //         break
    //       case 4:
    //         type = 'Client review'
    //         break
    //       case 5:
    //         type = 'Resource report'
    //         break
    //     }
    //     task.messages.push({
    //       author: o.fullName,
    //       authorID: o.creatorid,
    //       text: Helpers.stripTags(o.evText),
    //       type: type,
    //       typeID: +o.tag,
    //       creationTime: moment(o.ctime).format('DD.MM.YYYY HH:mm'),
    //     })
    //   })
    // }
    const config = configPool.config(task.prj_id)
    if (!config) return
    this.selectedTask = task
    this.selectedAttachmentID = null
    if (
      (this.netMode == NET_MODE.NETWORK || this.netMode == NET_MODE.LOCAL) &&
      !this.selectedTask.filePath
    ) {
      try {
        this.selectedTask.filePath = config.getFilePath(task)
        this.selectedTask.projectPath = config.getProjectPath(task)
      } catch (e) {
        LogError(e)
        this.$Message.error(e.message)
      }
    }
    if (task.attachments === null) {
      let attachments = await DB.getTaskAttachments(task.uid)
      attachments = _.filter(attachments, o => {
        var fileFormat = path.extname(o.originalfilename).toLowerCase()
        var tag = this.isRemoteMode ? 0 : 5
        return fileFormat == FILE_FORMATS[HOST_ID] && o.tag == tag
      })
      var prefix = config.getVersionPrefix(task)

      for (const attachment of attachments) {
        attachment.filename = path.basename(attachment.originalfilename)
        attachment.created = moment(attachment.creationtime).format(
          'DD.MM.YYYY HH:mm',
        )
        attachment.added = moment(attachment.creationtime).calendar()
        attachment.thumbPath = ''
        attachment.thumbHash64 = Helpers.hash16to64(attachment.thumbHash)
        attachment.hash64 = Helpers.hash16to64(attachment.hash)
        attachment.filepath = Helpers.pathJoin(
          this.downloadFolder,
          task.parent,
          task.name,
        )
        var thumbPath = Helpers.pathJoin(
          this.thumbsDir,
          attachment.thumbHash + '.png',
        )
        if (attachment.thumbHash) {
          if (fs.existsSync(thumbPath)) attachment.thumbPath = thumbPath
          else {
            Helpers.downloadFile(
              attachment.thumbHash,
              thumbPath,
              Helpers.pathJoin(task.parent, task.name),
              this.httpHosts,
            )
              .then(() => (attachment.thumbPath = thumbPath))
              .catch(error => {
                LogError(error)
              })
          }
        }
      }
      task.attachments = attachments
    }
  }
  actionSelectAttachment(attachment, localFile) {
    if (
      this.selectedAttachmentID &&
      this.selectedAttachmentID.attachment &&
      this.selectedAttachmentID.attachment.uid === attachment.uid
    ) {
      this.selectedAttachmentID = null
    } else {
      this.selectedAttachmentID = {
        attachment: attachment,
        localFile: localFile,
      }
    }
  }
  async openChildrenTask(task) {
    if (!task.hasChild) return
    var previd = this.browserTaskID
    this.browserTaskID = task.uid
    await this.updateTasks(false)
    this.browserHistory.push({
      name: task.name,
      id: previd,
    })
  }
  async browserBack() {
    this.browserTaskID = _.last(this.browserHistory).id
    await this.updateTasks(false)
    this.browserHistory.pop()
  }
  findDBFile(condition) {
    return new Promise((resolve, reject) => {
      this.db.findOne(condition, (error, attachment) => {
        if (error) return reject(Error(error))
        if (!attachment) return reject(Error('File not found'))
        return resolve(attachment)
      })
    })
  }
  async takeSnapshot(filePath, snapshotPath) {
    const result = await HostApp.snapshot(snapshotPath, 512)
    if (result !== true) throw Error('Can`t take snapshot')
    await Helpers.sleep()
  }
  async generateJPEGFile(fileName) {
    if (!fileName) return null
    fileName = Helpers.toCorrectPath(fileName)
    const result = await HostApp.jpegFile(fileName)
    if (result !== true) throw Error('generateJPEGFile error')
    return result
  }
  async generatePDFFile(fileName) {
    if (!fileName) return null
    fileName = Helpers.toCorrectPath(fileName)
    const result = await HostApp.pdfFile(fileName)
    if (result !== true) throw Error('generatePDFFile error')
    return result
  }
  async openPublishWindow(type) {
    try {
      this.PWData.type = type
      this.PWData.attachments = []
      this.PWData.hours = 10
      this.PWData.text = ''
      this.PWData.snapshot = Helpers.pathJoin(this.tempDir, 'snapshot.png')
      var fileInfo: any = null
      var task: any = null
      var filename = ''
      var filePath = Helpers.toCorrectPath(await HostApp.getFilename())
      fileInfo = this.openedFiles.config[filePath]
      if (!fileInfo) throw Error('File not opened')
      task = _.find(_.concat(this.tasks, this.browserTasks), [
        'uid',
        fileInfo.id,
      ])
      if (!task) {
        task = await DB.getTask(fileInfo.id)
        if (!task) throw Error('Task not found')
        await configPool.add(task.prj_id, this.downloadFolder)
      }
      const config = configPool.config(task.prj_id)
      if (!config) throw Error('Config not configure')
      const netMode = config.getNetmode()
      const isRemoteMode = netMode === NET_MODE.REMOTE
      this.PWData.task = task
      this.PWData.statusID = task.cc_status || task.status_uid
      var prefix = isRemoteMode ? '' : config.getVersionPrefix(task)
      var regex = isRemoteMode ? /_v\d+/g : new RegExp(`${prefix}\\d+`, 'g')
      filename = path
        .basename(filePath, path.extname(filePath))
        .replace(regex, '')
        .replace('.vlocal', '')

      this.PWData.extension = path.extname(filePath)
      var projectPath = isRemoteMode
        ? Helpers.pathJoin(this.downloadFolder, task.parent, task.name)
        : config.getValidPath(task)
      var publishFolder = Helpers.pathJoin(
        projectPath,
        config.getFullPublishPath(task),
      )
      if (isRemoteMode) {
        var attachments = await DB.getTaskAttachments(fileInfo.id)
        var _filename = path
          .basename(filename, path.extname(filename))
          .replace(/_v\d+/g, '')
          .replace('.vlocal', '')
        attachments = _.filter(
          attachments,
          o => o.originalfilename.indexOf(_filename + '_v') == 0,
        )
        var version: any =
          _.max(
            _.map(
              attachments,
              o => +(o.originalfilename.match(/_v(\d+)/) || [0, 0])[1],
            ),
          ) || 0
        this.PWData.filename = _filename
        this.PWData.prefixedVersion =
          '_v' + ('' + (version + 1)).padStart(2, '0')
      } else {
        if (!config.getFilePath(task)) throw new Error('Task not configure')
        prefix = config.getVersionPrefix(task)
        var padding = config.getVersionPadding(task)
        var extension = this.PWData.extension
        regex = new RegExp(`${prefix}(\\d{${padding}})\\${extension}`)
        attachments = []
        var versionFolder = config.getVersionFolder(task)
        if (fs.existsSync(versionFolder)) {
          var files = fs.readdirSync(versionFolder)
          attachments = _.filter(files, o => o.indexOf(filename + prefix) == 0)
        }
        version =
          '' +
          ((_.max(_.map(attachments, o => +(o.match(regex) || [0, 0])[1])) ||
            0) +
            1)
        this.PWData.filename = filename
        this.PWData.prefixedVersion = prefix + version.padStart(padding, '0')
      }
      var statuses = (await DB.getTaskStatuses(fileInfo.id)) || []
      this.PWData.statuses = statuses
      if (config.getPublishStatus(task)) {
        var publishStatus = config.getPublishStatus(task)
        var status = statuses.find(o => o.name === publishStatus)
        if (status && type === TYPE_MODAL.PUBLISH) {
          this.PWData.statusID = status.uid
        }
      }
      await this.takeSnapshot(filePath, this.PWData.snapshot)
      const filenames: string[] = config.filenames(task)
      const editable = config.filenameEditable(task)
      this.PWData.filenames = filenames
      this.PWData.editable = editable
      this.PWData.visible = true
    } catch (e) {
      this.$Message.error(e.message)
      console.error(e)
    }
  }
  actionClosePublishWindow() {
    this.PWData.visible = false
    this.PWData.loading = false
  }
  async actionPublishFile() {
    try {
      var task = this.PWData.task
      if (!task) throw new Error('Task not found')
      const config = configPool.config(task.prj_id)
      if (!config) throw new Error('Task not configured')
      const netMode = config.getNetmode()
      const isRemoteMode = netMode === NET_MODE.REMOTE
      this.PWData.loading = true
      const preVProcessor = config.getProcessor('version_pre')
      const replaceVProcessor = config.getProcessor('version_replace')
      const postVProcessor = config.getProcessor('version_post')
      const prePProcessor = config.getProcessor('publish_pre')
      const replacePProcessor = config.getProcessor('publish_replace')
      const postPProcessor = config.getProcessor('publish_post')
      let processorResult = null
      const taskInfo = Helpers.getTaskInfo(task, this.usid, this.username)

      var url = Helpers.pathJoin(task.parent, task.name) + '/'
      var message = this.PWData.text
      var statusID = this.PWData.statusID
      var messageType = 2
      var hours = this.PWData.hours
      var fileHash: string | null = null
      var thumbHash: string = 'null'
      var tag = 5
      var fileSize = 0
      var filePath = Helpers.toCorrectPath(await HostApp.getFilename())
      var displayFilename =
        this.PWData.filename +
        this.PWData.prefixedVersion +
        this.PWData.extension
      var snapshotpath = Helpers.toCorrectPath(this.PWData.snapshot)
      let [links, attachments] = _.partition(this.PWData.attachments, 'link')

      const fp = config.getFilePath(task)

      var versionFilename = ''
      var publishFilename = ''
      if (!isRemoteMode && fp) {
        var prefix = fp.ver_prefix || '_v'
        var regex = new RegExp(`${prefix}(\\d+)`, 'g')
        versionFilename = config.getFileVersionFolder(task, displayFilename)
        publishFilename = config.getFilePublishFolder(
          task,
          displayFilename.replace(regex, ''),
        )
      }
      if (isRemoteMode) {
        fileSize = fs.statSync(filePath).size
        tag = 0
      }

      processorResult = null
      const dialogType = this.PWData.type
      let processor =
        dialogType == TYPE_MODAL.VERSION ? preVProcessor : prePProcessor
      if (processor) {
        processorResult = await processor.runMethod(undefined, taskInfo, {
          localFilePath: filePath,
          versionFilePath: versionFilename,
          publishFilePath:
            dialogType == TYPE_MODAL.PUBLISH ? publishFilename : '',
          report: {
            plain_text: message,
            work_time: hours,
            attachments,
            links,
          },
        })
      }
      if (processorResult) {
        let {
          localFilePath,
          versionFilePath,
          publishFilePath,
          report: {
            plain_text,
            work_time,
            attachments: _attachments,
            links: _links,
          },
        } = processorResult
        filePath = localFilePath
        versionFilename = versionFilePath
        publishFilename = publishFilePath
        message = plain_text
        hours = work_time
        attachments = _attachments
        links = _links
      }

      processorResult = null
      processor =
        dialogType == TYPE_MODAL.VERSION ? replaceVProcessor : replacePProcessor
      if (processor) {
        processorResult = await processor.runMethod(undefined, taskInfo, {
          localFilePath: filePath,
          versionFilePath: versionFilename,
          publishFilePath:
            dialogType == TYPE_MODAL.PUBLISH ? publishFilename : '',
          report: {
            plain_text: message,
            work_time: hours,
            attachments,
            links,
          },
        })
      }

      if (!processorResult) {
        thumbHash = await CargadorAPI.importFile(
          this.httpHosts,
          snapshotpath,
          'thumbnail.cache',
        )
        let _fileHash = ''
        if (isRemoteMode) {
          _fileHash = await CargadorAPI.importFile(
            this.httpHosts,
            filePath,
            url,
          )
        }
        if (_fileHash) fileHash = _fileHash
        if (netMode == NET_MODE.NETWORK)
          fs.renameSync(filePath, versionFilename)
        if (netMode == NET_MODE.LOCAL)
          Helpers.copyFileSync(filePath, versionFilename)

        var files: ATTACHMENT[] = []
        for (const o of attachments) {
          files.push({
            hash: await CargadorAPI.importFile(this.httpHosts, o.filename, url),
            tag: ATTACHMENT_TAG.FILE,
            size: fs.statSync(o.filename).size,
            filename: o.filename,
            description: '',
            thumbnails: [],
          })
        }
        for (const o of links) {
          files.push({
            hash: null,
            tag: ATTACHMENT_TAG.LINK,
            size: 0,
            filename: o.filename,
            description: '',
            thumbnails: [],
          })
        }
        let thumbsPaths: string[][] = []
        for (const file of files) {
          try {
            thumbsPaths = [
              ...thumbsPaths,
              await config.generateThumbnail(
                file.filename,
                path.dirname(this.PWData.snapshot),
              ),
            ]
          } catch (e) {
            thumbsPaths = [...thumbsPaths, []]
          }
        }
        const thumbsPromises = thumbsPaths.map(paths =>
          Promise.all(
            paths.map(thumb =>
              CargadorAPI.importFile(this.httpHosts, thumb, 'thumbnail.cache'),
            ),
          ),
        )

        const thumbs = await Promise.all(thumbsPromises)

        files.forEach((file, i) => (file.thumbnails = thumbs[i] || []))

        files = [
          {
            hash: fileHash,
            tag,
            size: fileSize,
            filename: tag == 5 ? versionFilename : displayFilename,
            description: '',
            thumbnails: [thumbHash],
          },
          ...files,
        ]
        const publishOptions: PUBLISH_OPTIONS = {
          tid: task.uid,
          msg: message,
          type: messageType,
          hours,
          attachments: files,
        }
        await DB.publishFile(publishOptions)
        if ((task.cc_status || task.status_uid) !== statusID) {
          const changeStatus = await this.changeStatusWindow()
          if (changeStatus) {
            await DB.setTaskStatus(task.uid, statusID)
          }
        }
        if (this.PWData.type == TYPE_MODAL.PUBLISH) {
          if (netMode == NET_MODE.NETWORK)
            Helpers.copyFileSync(versionFilename, publishFilename)
          else if (netMode == NET_MODE.LOCAL)
            Helpers.copyFileSync(filePath, publishFilename)
        }
        this.$Message.success('File published')
      }

      processorResult = null
      processor =
        dialogType == TYPE_MODAL.VERSION ? postVProcessor : postPProcessor
      if (processor) {
        processorResult = await processor.runMethod(undefined, taskInfo, {
          localFilePath: filePath,
          versionFilePath: versionFilename,
          publishFilePath:
            dialogType == TYPE_MODAL.PUBLISH ? publishFilename : '',
          report: {
            plain_text: message,
            work_time: hours,
            attachments,
            links,
          },
        })
      }

      this.actionClosePublishWindow()
    } catch (error) {
      Log(error)
      this.$Message.error(error.message)
    } finally {
      this.PWData.loading = false
    }
  }

  changeStatusWindow() {
    return new Promise(resolve => {
      this.$Modal.confirm({
        title: 'Warning',
        content: '<p>Do you want to change task status?</p>',
        okText: 'Yes',
        cancelText: 'No',
        onOk: () => resolve(true),
        onCancel: () => resolve(false),
      })
    })
  }

  promptFilename(options: ChooseFilenameDialog): Promise<string | boolean> {
    const chooseFilenameWindow = <any>this.$refs['chooseFilenameWindow']
    if (!options.filename) {
      if (Array.isArray(options.filenames) && options.filenames.length > 0)
        options.filename = options.filenames[0]
      if (!Array.isArray(options.filenames))
        options.filename = options.filenames
    }
    this.chooseFilenameWindowData = {
      ...options,
      visible: true,
    }
    return new Promise((resolve, reject) => {
      chooseFilenameWindow.ok = () => {
        const filename = this.chooseFilenameWindowData.filename
        this.chooseFilenameWindowData = {
          visible: false,
          editable: false,
          filename: '',
          filenames: [],
        }
        resolve(filename)
      }
      chooseFilenameWindow.cancel = () => {
        this.chooseFilenameWindowData = {
          visible: false,
          editable: false,
          filename: '',
          filenames: [],
        }
        resolve(false)
      }
    })
  }

  async createFile() {
    var task = this.selectedTask
    if (!task) throw Error('Not selected task')
    const config = configPool.config(task.prj_id)
    if (!config) throw Error('Config not configure')
    let localFilePath: string = ''
    let filename = ''
    const filenames: string[] = config.filenames(task)
    if (filenames.length === 0 && !config.filenameEditable(task)) {
      filename = task.name
    } else if (filenames.length === 1 && !config.filenameEditable(task)) {
      filename = filenames[0]
    } else {
      const editable = config.filenameEditable(task)
      const result = await this.promptFilename({
        editable,
        filenames,
      })
      if (!result) return
      filename = <string>result
    }
    const taskInfo = Helpers.getTaskInfo(task, this.usid, this.username)
    const extension = FILE_FORMATS[HOST_ID]
    const fullFilename = `${filename}.vlocal${extension}`
    let filepath = ''
    if (this.netMode == NET_MODE.NETWORK && config.getValidPath(task)) {
      filepath =
        config.getFileVersionFolder(task, fullFilename) ||
        config.getFilePublishFolder(task, fullFilename)
      localFilePath = Helpers.pathJoin(filepath)
    } else if (
      this.netMode == NET_MODE.LOCAL ||
      this.netMode == NET_MODE.REMOTE
    ) {
      filepath = Helpers.pathJoin(task.parent, task.name, fullFilename)
      localFilePath = Helpers.pathJoin(this.downloadFolder, filepath)
    }
    let fileInfo = { localFilePath, originalFileName: localFilePath }
    const preProcessor = config.getProcessor('new_pre')
    let preResult: any = null
    if (preProcessor) {
      preResult = await preProcessor.runMethod(undefined, taskInfo, fileInfo)
      if (preResult && preResult.localFilePath) {
        localFilePath = Helpers.toCorrectPath(preResult.localFilePath)
      }
    }

    const replaceProcessor = config.getProcessor('new_replace')
    let replaceResult: any = null
    if (replaceProcessor) {
      replaceResult = await replaceProcessor.runMethod(
        undefined,
        taskInfo,
        fileInfo,
      )
      if (replaceResult && replaceResult.localFilePath) {
        localFilePath = Helpers.toCorrectPath(replaceResult.localFilePath)
      }
    }
    if (replaceResult === null) {
      Helpers.makePath(path.dirname(localFilePath))
      await HostApp.createFile(localFilePath)
    }

    const postProcessor = config.getProcessor('new_post')
    if (postProcessor) postProcessor.runMethod(undefined, taskInfo, fileInfo)
    localFilePath = await HostApp.getFilename()
    this.updateOpenedFiles(Helpers.toCorrectPath(localFilePath), task.uid, 0)
    Helpers.dispatchEvent('updateOpenedFiles')
  }

  async takeTaskToWork() {
    const task = this.selectedTask
    if (!task) throw Error('Task not select')
    const config = configPool.config(task.prj_id)
    if (!config || !config.validateTask(task))
      throw Error('Task config not configred')
    if ((+task.status.flags & 4) == 4) return
    const workStatus = _.find(task.statuses, o => (+o.flags & 4) == 4)
    if (!workStatus) throw Error('Can`t change status')
    const result = await DB.setTaskStatus(task.uid, workStatus.uid)
    const statusID = await DB.getTaskStatus(task.uid)
    if (workStatus.uid == statusID) return
    else throw Error('Can`t change status')
  }

  updateOpenedFiles(filename, taskId, version) {
    this.openedFiles.config[Helpers.pathNormalize(filename)] = {
      id: taskId ? taskId : this.selectedTask ? this.selectedTask.uid : -1,
      version: version ? +version : 0,
    }
    this.openedFiles.save()
  }
  async openFile(attachment) {
    if (!attachment) throw Error('Attachment is empty')
    const task = this.selectedTask
    if (!task) throw Error('Task not select')
    const config = configPool.config(task.prj_id)
    if (!config) throw Error('Config not configure')
    const preProcessor = config.getProcessor('open_pre')
    const replaceProcessor = config.getProcessor('open_replace')
    const postProcessor = config.getProcessor('open_post')
    let processorResult: any = null
    const taskInfo = {
      id: task.uid,
      name: task.name,
      parentId: task.parent_uid,
      parentPath: task.parent,
      statusId: task.status.uid,
      statusName: task.status.name,
      activityId: task.acivityid,
      activityName: task.activity,
      currentUserId: this.usid,
      currentUserName: this.username,
    }
    const prefix = config.getVersionPrefix(task)
    const regex = new RegExp(`${prefix}(\\d+)[^\\d]*$`, 'g')
    const fileextension = path.extname(attachment.originalfilename)
    let filename = path
      .basename(attachment.originalfilename, fileextension)
      .replace(regex, '')
      .replace('.vlocal', '')
    let localFilePath = ''
    if (!this.isRemoteMode) {
      localFilePath =
        config.getLocalFilePath(
          task,
          attachment.originalfilename,
          this.downloadFolder,
        ) || ''
    } else {
      localFilePath = Helpers.pathJoin(
        this.downloadFolder,
        task.parent,
        task.name,
        filename + '.vlocal' + fileextension,
      )
    }
    localFilePath = Helpers.toCorrectPath(localFilePath)
    var localFileDirectory = Helpers.toCorrectPath(path.dirname(localFilePath))
    let filepath = ''
    if (!this.isRemoteMode) {
      filepath = attachment.originalfilename
    } else {
      const file: any = await Helpers.findFile(this.db, {
        hash: attachment.hash,
        path: attachment.filepath,
        originalname: attachment.originalfilename,
      })
      filepath = Helpers.pathJoin(file.path, file.displayname)
    }
    Helpers.makePath(localFileDirectory)
    fs.copySync(filepath, localFilePath)
    processorResult = null
    if (preProcessor) {
      processorResult = await preProcessor.runMethod(undefined, taskInfo, {
        localFilePath: localFilePath,
        originalFileName: filepath,
      })
    }
    if (processorResult && processorResult.localFilePath) {
      localFilePath = Helpers.toCorrectPath(processorResult.localFilePath)
    }

    processorResult = null
    if (replaceProcessor) {
      processorResult = await replaceProcessor.runMethod(undefined, taskInfo, {
        localFilePath: localFilePath,
        originalFileName: filepath,
      })
    }
    if (!processorResult) {
      const openResult = await HostApp.openFile(localFilePath)
      if (openResult !== true) {
        throw Error('Host cant`t open file')
      }
    } else if (processorResult && processorResult.localFilePath) {
      localFilePath = Helpers.toCorrectPath(processorResult.localFilePath)
    }

    processorResult = null
    if (postProcessor) {
      processorResult = await postProcessor.runMethod(undefined, taskInfo, {
        localFilePath: localFilePath,
        originalFileName: filepath,
      })
    }
    if (processorResult && processorResult.localFilePath) {
      localFilePath = Helpers.toCorrectPath(processorResult.localFilePath)
    }
    if (attachment.parent) {
      attachment.parent.localFile = {
        uid: -1,
        filename: path.basename(localFilePath),
      }
    } else {
      attachment.localFile = {
        uid: -1,
        filename: path.basename(localFilePath),
      }
    }

    var version = 0
    var match = regex.exec(path.basename(filepath))
    if (match) {
      version = +match[1]
    } else version = 1
    this.updateOpenedFiles(localFilePath, task.uid, version)
    Helpers.dispatchEvent('updateOpenedFiles')
  }

  async downloadFile(attachment) {
    if (!attachment) throw Error('Attachment is null')
    if (!this.downloadFolder) throw Error('Download folder not set')
    if (!this.selectedTask) throw Error('Task not selected')
    const task = this.selectedTask
    const url = Helpers.pathJoin(task.parent, task.name)
    let count = await Helpers.countFile(this.db, {
      hash: attachment.hash,
      path: attachment.filepath,
      originalname: attachment.originalfilename,
    })
    if (count != 0) {
      return { result: 'ok' }
    }
    const attachments: any[] = await Helpers.findFile(this.db, {
      originalname: attachment.originalfilename,
      path: attachment.filepath,
    })
    count =
      attachments && attachments.length > 0
        ? 1 +
          Math.max.apply(
            null,
            attachments.map(o => {
              var match = o.displayname.match(/(_(\d+)|_(\d+)\..+)$/)
              return match ? +match[2] || +match[3] : 1
            }),
          )
        : 0
    var extname = path.extname(attachment.originalfilename)
    var basename = path.basename(attachment.originalfilename, extname)
    var displayname =
      count == 0
        ? attachment.originalfilename
        : `${basename}_${count}${extname}`
    attachment.downloading = true
    return Helpers.downloadFile(
      attachment.hash,
      Helpers.pathJoin(attachment.filepath, displayname),
      url,
      this.httpHosts,
    )
      .then(() => {
        attachment.downloaded = true
        attachment.downloading = false
        this.db.insert(
          {
            hash: attachment.hash,
            path: attachment.filepath,
            originalname: attachment.originalfilename,
            displayname: displayname,
          },
          (error, newAttach) => {
            if (error) {
              LogError(Error(error))
              throw Error(error)
            }
          },
        )
      })
      .catch(error => {
        attachment.downloading = false
        throw Error(error)
      })
  }
  async updateTasks(isTodo) {
    /* Side panel loading on */
    if (isTodo) this.todoLoading = true
    else this.browserLoading = true

    /* Get db tasks */
    var tasks = await (isTodo
      ? DB.getTodoTasks(this.usid)
      : DB.getChildTasks(this.browserTaskID))
    if (!tasks) return
    // if (isTodo) {
    //   tasks.forEach(task => {
    //     const messages = _.chain(task.events)
    //       .orderBy('created_at_js', 'asc')
    //       .filter(o => o.tag !== 6)
    //       .filter(
    //         o =>
    //           typeof o.text_html_plain === 'string' &&
    //           o.text_html_plain.trim() !== '',
    //       )
    //       .map(o => ({
    //         author: o.creator_name,
    //         authorID: o.creator_uid,
    //         text: Helpers.stripTags(o.text_html_plain),
    //         type: Helpers.msgTagToStr(o.tag),
    //         typeID: o.tag,
    //         creationTime: moment(o.created_at_js).format('DD.MM.YYYY HH:mm'),
    //       }))
    //       .value()
    //   })
    // }
    for (let task of tasks) {
      const url = Helpers.pathJoin(task.parent, task.name)
      try {
        await configPool.add(task.prj_id, this.downloadFolder)
      } catch (error) {
        console.error(error)
      }
      Helpers.resetTaskData(task)
      const parentParts =
        (typeof task.parent === 'string' &&
          task.parent.split('/').filter(o => o)) ||
        []
      task.parentTaskName =
        parentParts.length > 0 ? parentParts[parentParts.length - 1] : ''
      task.projectName = parentParts.length > 0 ? parentParts[0] : ''
      task.status = _.find(this.statuses, ['uid', task.status_uid])
      task.thumbPath = ''
      task.thumbHash64 = Helpers.hash16to64(task.thumbHash)
      task.deadline = Helpers.getTaskDeadline(task)
      task.stop = task.deadline.calendar()
      let thumbPath = Helpers.getTaskThumbPath(task, this.thumbsDir)
      if (fs.existsSync(thumbPath)) {
        task.thumbPath = thumbPath
      } else {
        if (task.thumbHash64) {
          Helpers.downloadFile(task.thumbHash, thumbPath, url, this.httpHosts)
            .then(() => {
              task.thumbPath = thumbPath
            })
            .catch(error => {
              LogError(error)
            })
        }
      }

      const lastEvent = _.chain(task.events)
        .sortBy('mtm_at_js')
        .filter({ tag: 6, statusid: task.status_uid })
        .last()
        .value()

      if (lastEvent && task.status && Helpers.bitTest(task.status.flags, 2)) {
        task.inWork = true
        task.inWorkTime = moment(lastEvent.created_at_js).format('DD.MM.YYYY')
        task.inWorkUsername = lastEvent.creator_name
        task.inWorkCreatorID = lastEvent.creator_uid
      }

      task.messages = _.chain(task.events)
        .orderBy('created_at_js', 'asc')
        .filter(o => o.tag !== 6)
        .filter(
          o =>
            typeof o.text_html_plain === 'string' &&
            o.text_html_plain.trim() !== '',
        )
        .map(o => ({
          author: o.creator_name,
          authorID: o.creator_uid,
          text: Helpers.stripTags(o.text_html_plain),
          type: Helpers.msgTagToStr(o.tag),
          typeID: o.tag,
          creationTime: moment(o.created_at_js).format('DD.MM.YYYY HH:mm'),
        }))
        .value()
      // if (isTodo) {
      //   const config = configPool.config(task.prj_id)
      //   const fileTag: number = (config && !config.isRemoteMode() && 5) || 0
      //   const isThumbFile = ({ tag }) => [1, 2, 3].includes(tag)
      //   let [thumbs, files] = _.partition(task.files, isThumbFile)
      //   console.log('fileTag', fileTag)
      //   files = _.filter(files, ['tag', fileTag])
      //   let thumbsGroups = _.groupBy(thumbs, 'groupid')
      //   thumbsGroups = _.map(thumbsGroups, o => _.orderBy('tag', 'asc'))
      //   _.each(
      //     files,
      //     o =>
      //       (o.thumbs =
      //         (thumbsGroups[o.groupid] &&
      //           _.map(thumbsGroups[o.groupid], 'hash')) ||
      //         []),
      //   )
      //   console.log(task.name, files)
      // }
    }
    if (isTodo) {
      this.tasks = tasks
      this.todoLoading = false
    } else {
      this.browserTasks = tasks
      this.browserLoading = false
    }
    if (this.selectedTask) this.onTaskSelect(this.selectedTask)
    if (this.openRPublishWindow === true) {
      this.openRPublishWindow = false
      this.openPublishWindow(TYPE_MODAL.PUBLISH)
    } else if (this.openReportWindow === true) {
      this.openReportWindow = false
    } else if (this.openSaveVersionWindow === true) {
      this.openSaveVersionWindow = false
      this.openPublishWindow(TYPE_MODAL.VERSION)
    }
  }
  async checkUpdates() {
    const mtm = await DB.getMTM()
    if (mtm) {
      const date = moment(mtm)
      if (this.lastMTM == +date) return
      this.lastMTM = +date
      this.updateTasks(true)
      this.updateTasks(false)
    } else {
      console.error('Couldn`t get last MTM')
    }
  }
}
</script>
