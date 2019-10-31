<template>
  <div>
    <Select v-if="selectMode" v-model="value" :disabled="disabled">
      <Option
        v-for="item in names"
        :value="item"
        :key="item"
        v-tooltip.auto="{ content: item, delay: 1000, classes: 'file-tooltip' }"
        >{{ item }}</Option
      >
    </Select>
    <AutoComplete
      v-else
      :disabled="disabled || disabledInput"
      v-model="value"
      placeholder="Filename"
    >
      <Option
        v-for="item in autocompleteNames"
        :value="item"
        :key="item"
        v-tooltip.auto="{ content: item, delay: 1000, classes: 'file-tooltip' }"
        >{{ item }}</Option
      >
    </AutoComplete>
  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'
import { TYPE_MODAL } from '@/pages/consts'
import path from 'path'

@Component
export default class FilenameInput extends Vue {
  @Prop() private disabled!: boolean
  @Prop() private name!: string
  @Prop() private names!: string | string[]
  @Prop() private editable!: boolean

  get autocompleteNames() {
    return Array.isArray(this.names) && this.names.length > 1
      ? this.names
      : null
  }

  get selectMode() {
    return Array.isArray(this.names) && this.names.length > 1 && !this.editable
  }

  get disabledInput() {
    return (
      (Array.isArray(this.names) &&
        this.names.length === 1 &&
        !this.editable) ||
      !this.editable
    )
  }

  get value() {
    return this.name
  }

  set value(value) {
    this.$emit('filename-changed', value || '')
  }
}
</script>
