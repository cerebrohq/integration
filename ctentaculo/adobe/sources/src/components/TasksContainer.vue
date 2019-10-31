<template>
  <div class="cards">
    <div
      class="card prevTask"
      @click="$emit('task-parent-open')"
      v-show="hasHistory"
    >
      <Button shape="circle" icon="ios-arrow-thin-left"></Button>
      <p>Back</p>
    </div>
    <Task
      v-for="task in _tasks"
      :key="task.uid"
      :task="task"
      :variant="variant"
      @select="$emit('task-select', task)"
      @open-menu="$emit('task-open-menu', $event, task)"
      @child-open="$emit('task-child-open', task)"
    />
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'
import Task from '@/components/Task.vue'

@Component({ components: { Task } })
export default class Sidebar extends Vue {
  @Prop() private tasks!: any[]
  @Prop() private selectedTask!: any
  @Prop() private breadcrumbs!: any[]
  @Prop() private variant!: string

  get _tasks() {
    return this.tasks.map(o => ({
      ...o,
      selected: this.selectedTask ? o.uid === this.selectedTask.uid : false,
    }))
  }

  get hasHistory() {
    return Array.isArray(this.breadcrumbs) && this.breadcrumbs.length > 0
  }
}
</script>
