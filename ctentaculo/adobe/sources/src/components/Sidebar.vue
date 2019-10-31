<template>
  <div class="side">
    <SearchPanel
      :search="search"
      :sort="sort"
      :breadcrumbs="breadcrumbs"
      @search-changed="$emit('search-changed', $event)"
      @sort-changed="$emit('sort-changed', $event)"
    />
    <TasksContainer
      :tasks="tasks"
      :selectedTask="selectedTask"
      :breadcrumbs="breadcrumbs"
      :variant="variant"
      @task-select="onTaskSelect"
      @task-open-menu="onTaskOpenMenu"
      @task-parent-open="$emit('task-parent-open')"
      @task-child-open="$emit('task-child-open', $event)"
    />
    <spin fix v-if="loading">
      <icon type="load-c" size="45" class="spin-icon-load"></icon>
    </spin>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'
import SearchPanel from '@/components/SearchPanel.vue'
import TasksContainer from '@/components/TasksContainer.vue'

@Component({ components: { SearchPanel, TasksContainer } })
export default class Sidebar extends Vue {
  @Prop() private loading!: boolean
  @Prop() private tasks!: any[]
  @Prop() private selectedTask!: any
  @Prop() private search!: string
  @Prop() private sort!: string
  @Prop() private breadcrumbs!: any[]
  @Prop() private variant!: string

  onTaskSelect(task) {
    this.$emit('task-select', task)
  }

  onTaskOpenMenu(event, task) {
    this.$emit('task-open-menu', event, task)
  }
}
</script>
