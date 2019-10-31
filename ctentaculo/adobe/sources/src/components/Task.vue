<template>
  <div
    class="card task"
    :class="{
      selected: task.selected,
    }"
    @click="$emit('select', task)"
    @dblclick="$emit('child-open', task)"
    @contextmenu.prevent="$emit('open-menu', $event, task)"
  >
    <div class="taskImage" :style="thumbStyle">
      <img
        class="folder"
        src="~@/assets/folder-overlay.png"
        v-show="task.hasChild"
      />
    </div>
    <div class="info">
      <template v-if="browserVariant">
        <p class="title">{{ name }}</p>
        <breadcrumb
          separator=">"
          v-tooltip.auto="{ content: parent, delay: 400 }"
        >
          <breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">{{
            item
          }}</breadcrumb-item>
        </breadcrumb>
      </template>
      <template v-else
        ><p class="title">{{ parentName }}</p>
        <span class="sub-title">{{ name }}</span>
        <breadcrumb
          separator=">"
          v-tooltip.auto="{ content: parent, delay: 400 }"
        >
          <breadcrumb-item>{{ project }}</breadcrumb-item>
        </breadcrumb>
      </template>
      <p class="deadline">
        Deadline:
        <span>{{ deadline }}</span>
      </p>
    </div>
    <div class="action">
      <img
        style="width: 16px; height: 16px"
        v-show="statusImg"
        :src="statusImg"
        v-tooltip.auto="statusName"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'

const IMG_PLACEHOLDER: string = require('@/assets/image-placeholder.png')

@Component
export default class Task extends Vue {
  @Prop() private task!: any
  @Prop() private variant!: string

  get browserVariant() {
    return this.variant === 'browser'
  }

  get thumbStyle() {
    if (this.task && this.task.thumbPath)
      return {
        'background-image': `url(${this.task.thumbPath})`,
      }
    return {
      'background-image': `url(${IMG_PLACEHOLDER})`,
      'background-size': '58px 36px',
    }
  }

  get parentName() {
    return (this.task && this.task.parentTaskName) || ''
  }

  get breadcrumbs() {
    return (
      (this.task &&
        this.task.parent &&
        this.task.parent.split('/').filter(o => o)) ||
      []
    )
  }

  get name() {
    return (this.task && this.task.name) || ''
  }

  get parent() {
    return (this.task && this.task.parent) || ''
  }

  get project() {
    return (this.task && this.task.projectName) || ''
  }

  get deadline() {
    return (this.task && this.task.stop) || ''
  }

  get statusImg() {
    return (
      (this.task && this.task.status && this.task.status.imgData) ||
      (this.task && this.task.status && this.task.status.thumb) ||
      ''
    )
  }

  get statusName() {
    return (this.task && this.task.status && this.task.status.name) || ''
  }
}
</script>
