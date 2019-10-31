<template>
  <modal
    :value="visible"
    @on-ok="ok"
    @on-cancel="cancel"
    title="Choose filename"
    ok-text="OK"
    cancel-text="Cancel"
    class-name="choosefilename"
  >
    <Form label-position="top">
      <FormItem label="Please choose filename">
        <FilenameInput
          class="filename-input"
          :name="filename"
          :names="filenames"
          :editable="editable"
          @filename-changed="$emit('filename-changed', $event)"
        />
      </FormItem>
    </Form>
  </modal>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'
import FilenameInput from '@/components/FilenameInput.vue'

interface IChooseFilenameOptions {
  filename: string
  filenames: string[]
  editable: boolean
}

@Component({ components: { FilenameInput } })
export default class СhooseFilenameWindow extends Vue {
  @Prop() private visible!: boolean
  @Prop() private filename!: string
  @Prop() private filenames!: string[]
  @Prop() private editable!: boolean

  ok() {
    this.$emit('ok')
  }

  cancel() {
    this.$emit('cancel')
  }
}
</script>
