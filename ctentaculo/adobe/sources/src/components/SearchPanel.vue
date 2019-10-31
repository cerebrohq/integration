<template>
  <div>
    <div class="sortPanel">
      <i-input
        clearable
        placeholder="Search"
        :value="search"
        @on-change="$emit('search-changed', $event.target.value)"
      >
        <icon slot="prepend" type="ios-search"></icon>
      </i-input>
      <v-popover
        container=".sortPanel"
        popover-base-class="tooltip popover filter-menu"
        style="left: 5px; right: 5px; top: 100%"
      >
        <Button
          class="tooltip-target"
          type="text"
          icon="ios-settings-strong"
          style="color: #fff; font-size: 20px"
        ></Button>
        <template slot="popover">
          <div class="sort">
            <p class="sort-label">Sort by:</p>
            <Select
              class="sort-type"
              placeholder="Sorting"
              :value="sort"
              @on-change="$emit('sort-changed', $event)"
            >
              <Option v-for="o in sortValues" :key="o.value" :value="o.value">{{
                o.caption
              }}</Option>
            </Select>
          </div>
        </template>
      </v-popover>
    </div>
    <breadcrumb v-if="hasHistory" separator=">">
      <breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index">{{
        item.name
      }}</breadcrumb-item>
    </breadcrumb>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'

interface ISortValue {
  value: string
  caption: string
}

@Component
export default class SearchPanel extends Vue {
  @Prop() private search!: string
  @Prop() private sort!: string
  @Prop() private breadcrumbs!: any[]

  sortValues: ISortValue[] = [
    { value: 'name', caption: 'Task name' },
    { value: 'status', caption: 'Status' },
    { value: 'activity', caption: 'Activity' },
    { value: 'deadline', caption: 'Deadline' },
    { value: 'order', caption: 'Order' },
    { value: 'parent', caption: 'Project' },
  ]

  get hasHistory() {
    return Array.isArray(this.breadcrumbs) && this.breadcrumbs.length > 0
  }
}
</script>
