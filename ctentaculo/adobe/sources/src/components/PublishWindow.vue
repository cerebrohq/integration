<template>
  <modal
    :value="visible"
    @on-cancel="$emit('close')"
    width="80"
    class-name="publishModal"
    :closable="!loading"
    :mask-closable="!loading"
  >
    <p slot="header">{{ title }}</p>
    <div class="modalContent">
      <div class="taskInfo">
        <p class="block-title">Task</p>
        <div class="taskInfo-content">
          <div class="taskImg" :style="thumbStyle"></div>
          <div class="taskInfo-block">
            <p class="task-title" v-if="taskName">{{ taskName }}</p>
            <breadcrumb separator=">" v-if="taskBreadcrumbs">
              <breadcrumb-item v-for="item in taskBreadcrumbs" :key="item">
                {{ item }}
              </breadcrumb-item>
            </breadcrumb>
          </div>
        </div>
      </div>
      <div class="publishInfo">
        <div class="aboutFile">
          <p class="block-title">File</p>
          <div class="filename-container ">
            <FilenameInput
              class="filename-input"
              :name="filename"
              :names="filenames"
              :editable="editable"
              :disabled="loading"
              @filename-changed="$emit('filename-changed', $event)"
            />
            <span>{{ filenameSuffix }}</span>
          </div>
          <div class="file-img" :style="snapshotStyle"></div>
        </div>
        <div class="aboutReport">
          <div class="report-input">
            <p class="block-title">Report</p>
            <Input
              type="textarea"
              :autosize="true"
              placeholder="Enter text"
              :value="text"
              :disabled="loading"
              @on-change="$emit('text-changed', $event.target.value)"
            />
          </div>
          <div class="report-attachments">
            <p class="block-title">Attachments</p>
            <div class="attachments-list">
              <div
                class="attachments-list-item"
                v-for="(attachment, i) in files"
                :key="i"
              >
                <div class="file-type">
                  <img v-if="attachment.link" src="~@/assets/local.png" />
                </div>
                <p
                  class="file-name"
                  v-tooltip.auto="{
                    content: attachment.filename,
                    delay: 1000,
                    classes: 'file-tooltip',
                  }"
                >
                  {{ attachment.displayname }}
                </p>
                <span class="action">
                  <Button
                    @click="$emit('remove-attachment', i)"
                    style="width:15px;height:15px;font-size:9px"
                    size="small"
                    type="error"
                    shape="circle"
                    icon="close-round"
                    :disabled="loading"
                  ></Button
                ></span>
              </div>
            </div>
            <div class="actions">
              <Button
                type="primary"
                shape="circle"
                @click="$emit('add-attachment', false)"
                :disabled="loading"
              >
                Add files
              </Button>
              <Button
                type="primary"
                shape="circle"
                @click="$emit('add-attachment', true)"
                :disabled="loading"
              >
                Add files as links
              </Button>
            </div>
          </div>
          <div class="report-status">
            <Form label-position="left" :label-width="70">
              <FormItem label="Status:">
                <Select
                  :value="statusID"
                  :disabled="loading"
                  @on-change="$emit('status-changed', $event)"
                  placeholder="Status"
                >
                  <Option
                    v-for="item in _statuses"
                    :value="item.uid"
                    :key="item.uid"
                  >
                    {{ item.name }}
                  </Option>
                </Select>
              </FormItem>
              <FormItem label="Work time:">
                <TimePicker
                  v-model="timePickerValue"
                  :steps="[1, 10]"
                  format="HH:mm"
                  placement="top"
                  placeholder="Work time"
                  :clearable="false"
                  :editable="false"
                  :disabled="loading"
                  :readonly="loading"
                />
              </FormItem>
            </Form>
          </div>
        </div>
      </div>
    </div>
    <div slot="footer" class="modal-footer-buttons">
      <Button
        type="ghost"
        shape="circle"
        @click="$emit('close')"
        :disabled="loading"
      >
        Cancel
      </Button>
      <Button
        type="primary"
        shape="circle"
        @click="$emit('ok')"
        :loading="loading"
      >
        {{ mainActionCaption }}
      </Button>
    </div>
  </modal>
</template>

<script lang="ts">
import { Component, Prop, Vue, Watch } from 'vue-property-decorator'
import { TYPE_MODAL } from '@/pages/consts'
import FilenameInput from '@/components/FilenameInput.vue'
import path from 'path'

const IMG_PLACEHOLDER: string = require('@/assets/image-placeholder.png')

@Component({ components: { FilenameInput } })
export default class PublishWindow extends Vue {
  @Prop() private visible!: boolean
  @Prop() private loading!: boolean
  @Prop() private type: TYPE_MODAL = TYPE_MODAL.VERSION
  @Prop() private task!: any
  @Prop() private statuses!: any[]
  @Prop() private statusID!: number
  @Prop() private attachments!: any[]
  @Prop() private snapshot!: string
  @Prop() private hours!: number
  @Prop() private text: string = ''
  @Prop() private filename!: string
  @Prop() private extension!: string
  @Prop() private prefixedVersion!: string
  @Prop() private filenames!: string | string[]
  @Prop() private editable!: boolean

  private query: string = ''

  @Watch('visible')
  onVisibleChanged(newVal, oldVal) {
    if (newVal === true && oldVal === false) {
      this.query = String(Date.now())
    }
  }

  get files() {
    return [...this.attachments].map(o => ({
      ...o,
      displayname: path.basename(o.filename),
    }))
  }

  get title() {
    return this.type == TYPE_MODAL.PUBLISH
      ? 'Publish'
      : this.type == TYPE_MODAL.VERSION
      ? 'Save version'
      : ''
  }

  get mainActionCaption() {
    return this.type == TYPE_MODAL.PUBLISH
      ? 'Publish'
      : this.type == TYPE_MODAL.VERSION
      ? 'Save as version'
      : ''
  }

  get taskName(): string {
    return (this.task && this.task.name) || ''
  }

  get taskBreadcrumbs(): string[] {
    return (
      this.task &&
      this.task.parent &&
      this.task.parent.split('/').filter(o => o)
    )
  }

  get filenameSuffix(): string {
    return `${this.prefixedVersion}${this.extension}`
  }

  get _statuses() {
    return (
      this.statuses &&
      this.statuses.map(o =>
        o.uid === null ? { ...o, uid: 0, name: 'No status' } : o,
      )
    )
  }

  get timePickerValue() {
    const hours = Math.floor(this.hours / 60)
    const minutes = this.hours % 60
    return new Date(0, 0, 0, hours, minutes)
  }

  set timePickerValue(value) {
    let [hours, minutes]: number[] | string[] = (<string>(
      (<unknown>value)
    )).split(':')
    hours = Number(hours.substring(0, 2))
    minutes = Number(minutes.substring(0, 2))
    if (!isNaN(hours) && !isNaN(minutes)) {
      const result = hours * 60 + minutes
      this.$emit('hours-changed', result)
    }
  }

  get thumbStyle() {
    if (!this.task || !this.task.thumbPath)
      return {
        'background-image': `url(${IMG_PLACEHOLDER})`,
        'background-size': '58px 36px',
      }
    return {
      'background-image': `url("${this.task.thumbPath}")`,
    }
  }

  get snapshotStyle() {
    if (!this.snapshot)
      return {
        'background-image': `url(${IMG_PLACEHOLDER})`,
        'background-size': '58px 36px',
      }
    return {
      'background-image': `url("file://${this.snapshot}?${this.query}")`,
    }
  }
}
</script>
