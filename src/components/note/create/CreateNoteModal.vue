<template>
  <div>
    <div :class="{'d-flex justify-content-center pl-3 pr-3': isBatchFeature}">
      <b-btn
        :id="isBatchFeature ? 'batch-note-button' : 'new-note-button'"
        :class="{'w-100': isBatchFeature}"
        :disabled="disableNewNoteButton"
        class="mt-1 mr-2 btn-primary-color-override btn-primary-color-override-opaque"
        variant="primary"
        @click="openNoteModal()">
        <span class="m-1">
          <font-awesome icon="file-alt" />
          <span class="sr-only">{{ isBatchFeature ? 'Batch create ' : 'Create ' }}</span>
          New Note
        </span>
      </b-btn>
    </div>
    <FocusLock
      v-if="isModalOpen"
      :disabled="isFocusLockDisabled"
      class="create-note-container">
      <div
        id="new-note-modal-container"
        :class="{
          'd-none': isNil(mode),
          'modal-content': includes(['batch', 'create', 'editTemplate'], mode),
          'mt-4': isBatchFeature
        }">
        <form @submit.prevent="submitForm()">
          <CreateNoteHeader :cancel-primary-modal="cancelRequested" />
          <hr class="m-0" />
          <div class="mt-2 mr-3 mb-1 ml-3">
            <transition v-if="isBatchFeature" name="batch">
              <div v-show="mode !== 'editTemplate'">
                <BatchNoteFeatures :cancel="cancelRequested" />
                <hr />
              </div>
            </transition>
            <div class="ml-2 mr-3 mt-2 pl-2 pr-2">
              <b-alert
                id="alert-in-note-modal"
                :show="dismissAlertSeconds"
                class="font-weight-bolder w-100"
                dismissible
                fade
                variant="info"
                aria-live="polite"
                role="alert"
                @dismiss-count-down="dismissAlert">
                <div class="d-flex">
                  <div v-if="isSaving" class="mr-2">
                    <font-awesome icon="sync" spin />
                  </div>
                  <div>{{ alert }}</div>
                </div>
              </b-alert>
            </div>
            <div>
              <label for="create-note-subject" class="font-size-14 font-weight-bolder mb-1"><span class="sr-only">Note </span>Subject</label>
            </div>
            <div>
              <input
                id="create-note-subject"
                :value="model.subject"
                :disabled="isSaving"
                :class="{ 'bg-light': isSaving }"
                aria-labelledby="create-note-subject-label"
                class="cohort-create-input-name"
                maxlength="255"
                type="text"
                @input="setSubjectPerEvent"
                @keydown.enter="submitForm()"
                @keydown.esc="cancelRequested()">
            </div>
            <div>
              <label for="create-note-body" class="font-size-14 font-weight-bolder mt-3 mb-1">Note Details</label>
            </div>
            <div id="note-details">
              <RichTextEditor
                id="create-note-body"
                :initial-value="model.body || ''"
                :disabled="isSaving"
                :is-in-modal="true"
                :on-value-update="setBody" />
            </div>
          </div>
          <div>
            <AdvisingNoteTopics
              :key="mode"
              :disabled="isSaving"
              :function-add="addTopic"
              :function-remove="removeTopic"
              :topics="model.topics"
              class="mt-2 mr-3 mb-1 ml-3" />
            <AdvisingNoteAttachments
              :add-attachment="addAttachment"
              :disabled="isSaving"
              :existing-attachments="model.attachments"
              :remove-attachment="removeAttachment"
              class="mt-2 mr-3 mb-1 ml-3" />
          </div>
          <hr />
          <div>
            <CreateNoteFooter
              :cancel="cancelRequested"
              :create-note="createNote"
              :save-as-template="saveAsTemplate"
              :update-template="updateTemplate" />
          </div>
        </form>
      </div>
    </FocusLock>
    <AreYouSureModal
      v-if="showDiscardNoteModal"
      :function-cancel="cancelDiscardNote"
      :function-confirm="discardNote"
      :show-modal="showDiscardNoteModal"
      modal-header="Discard unsaved note?" />
    <CreateTemplateModal
      :show-modal="showCreateTemplateModal"
      :cancel="cancelCreateTemplate"
      :create="createTemplate"
      :toggle-show="toggleShowCreateTemplateModal" />
    <AreYouSureModal
      v-if="showDiscardTemplateModal"
      :function-cancel="cancelDiscardTemplate"
      :function-confirm="discardTemplate"
      :show-modal="showDiscardTemplateModal"
      modal-header="Discard unsaved template?" />
  </div>
</template>

<script>
import AdvisingNoteAttachments from '@/components/note/AdvisingNoteAttachments';
import AdvisingNoteTopics from '@/components/note/AdvisingNoteTopics';
import AreYouSureModal from '@/components/util/AreYouSureModal';
import BatchNoteFeatures from '@/components/note/create/BatchNoteFeatures';
import Context from '@/mixins/Context';
import CreateNoteFooter from '@/components/note/create/CreateNoteFooter';
import CreateNoteHeader from '@/components/note/create/CreateNoteHeader';
import CreateTemplateModal from "@/components/note/create/CreateTemplateModal";
import FocusLock from 'vue-focus-lock';
import NoteEditSession from '@/mixins/NoteEditSession';
import RichTextEditor from '@/components/util/RichTextEditor';
import store from "@/store";
import Util from '@/mixins/Util';
import Vue from "vue"
import { createNoteTemplate, updateNoteTemplate } from '@/api/note-templates';

export default {
  name: 'CreateNoteModal',
  components: {
    AdvisingNoteAttachments,
    AdvisingNoteTopics,
    AreYouSureModal,
    BatchNoteFeatures,
    CreateNoteFooter,
    CreateNoteHeader,
    CreateTemplateModal,
    FocusLock,
    RichTextEditor
  },
  mixins: [Context, NoteEditSession, Util],
  props: {
    student: {
      required: false,
      type: Object
    }
  },
  data: () => ({
    alert: undefined,
    dismissAlertSeconds: 0,
    isBatchFeature: undefined,
    isModalOpen: false,
    showCreateTemplateModal: false,
    showDiscardNoteModal: false,
    showDiscardTemplateModal: false,
    showErrorPopover: false
  }),
  mounted() {
    this.isBatchFeature = !this.student;
    store.dispatch('noteEditSession/loadNoteTemplates');
  },
  methods: {
    cancelRequested() {
      if (this.mode === 'editTemplate') {
        const indexOf = this.noteTemplates.findIndex(t => t.id === this.model.id);
        const template = this.noteTemplates[indexOf];
        const noDiff = this.trim(this.model.subject) === template.subject
          && this.model.body === template.body
          && !this.size(this.xor(this.model.topics, template.topics))
          && !this.size(this.xorBy(this.model.attachments, template.attachments, 'displayName'));
        if (noDiff) {
          this.discardTemplate();
        } else {
          this.showDiscardTemplateModal = true;
          this.setFocusLockDisabled(true);
        }
      } else {
        const unsavedChanges = this.trim(this.model.subject)
          || this.stripHtmlAndTrim(this.model.body)
          || this.size(this.model.topics)
          || this.size(this.model.attachments)
          || this.addedCohorts.length
          || this.addedCuratedGroups.length;
        if (unsavedChanges) {
          this.showDiscardNoteModal = true;
          this.setFocusLockDisabled(true);
        } else {
          this.discardNote();
        }
      }
    },
    cancelCreateTemplate() {
      this.showCreateTemplateModal = false;
      this.setFocusLockDisabled(false);
    },
    cancelDiscardNote() {
      this.showDiscardNoteModal = false;
      this.setFocusLockDisabled(false);
      this.putFocusNextTick('create-note-subject');
      this.alertScreenReader(`Continue editing note.`);
    },
    cancelDiscardTemplate() {
      this.showDiscardTemplateModal = false;
      this.setFocusLockDisabled(false);
      this.putFocusNextTick('create-note-subject');
    },
    createNote() {
      if (this.model.subject && this.targetStudentCount) {
        this.setIsSaving(true);
        this.onCreateNoteStart(this.model.subject);
        if (this.model.attachments.length) {
          // File upload might take time; alert will be overwritten when API call is done.
          this.showAlert('Creating note...', 60);
        }
        this.isModalOpen = false;
        this.createAdvisingNotes().then(data => {
          this.setIsSaving(false);
          this.exit();
          // After modal is closed...
          this.onCreateNoteSuccess();
          this.alertScreenReader(this.isBatchFeature ? `Note created for ${this.targetStudentCount} students.` : "New note saved.");
          const uid = this.$currentUser.uid;
          if (this.isBatchFeature) {
            Vue.prototype.$eventHub.$emit('batch-of-notes-created', data);
            Vue.prototype.$ga.noteEvent(data.id, `Advisor ${uid} created a batch of notes`, 'batch_create');
          } else {
            Vue.prototype.$eventHub.$emit('advising-note-created', data);
            Vue.prototype.$ga.noteEvent(data.id, `Advisor ${uid} created a note`, 'create');
          }
        });
      }
    },
    createTemplate(title) {
      this.showCreateTemplateModal = false;
      this.setIsSaving(true);
      this.setFocusLockDisabled(false);
      if (this.model.attachments.length) {
        // File upload might take time; alert will be overwritten when API call is done.
        this.showAlert('Creating template...', 60);
      }
      createNoteTemplate(title, this.model.subject, this.model.body, this.model.topics, this.model.attachments).then(template => {
        this.showAlert(`Template '${title}' created.`);
        this.setIsSaving(false);
        this.setModel({
          id: undefined,
          subject: template.subject,
          body: template.body,
          topics: template.topics,
          attachments: template.attachments,
          deleteAttachmentIds: []
        });
        this.setMode(this.isBatchFeature ? 'batch' : 'create');
        this.putFocusNextTick('create-note-subject');
      });
    },
    discardNote() {
      this.showDiscardNoteModal = false;
      this.setFocusLockDisabled(false);
      this.isModalOpen = false;
      this.dismissAlertSeconds = 0;
      this.alertScreenReader('Cancelled create new note');
      this.exit();
    },
    discardTemplate() {
      this.showDiscardTemplateModal = false;
      this.setFocusLockDisabled(false);
      this.resetModel();
      this.setMode(this.isBatchFeature ? 'batch' : 'create');
      this.putFocusNextTick('create-note-subject');
      this.alertScreenReader('Cancelled create template.');
    },
    dismissAlert(seconds) {
      this.dismissAlertSeconds = seconds;
      if (seconds === 0) {
        this.alert = undefined;
      }
    },
    exit() {
      this.alert = this.dismissAlertSeconds = undefined;
      this.isModalOpen = this.showCreateTemplateModal = this.showDiscardNoteModal = this.showDiscardTemplateModal = this.showErrorPopover = false;
      this.exitSession();
    },
    openNoteModal() {
      this.resetModel();
      const sid = this.get(this.student, 'sid');
      if (sid) {
        this.addSid(sid);
      }
      this.setMode(this.isBatchFeature ? 'batch' : 'create');
      this.isModalOpen = true;
      this.putFocusNextTick(this.isBatchFeature ? 'create-note-add-student-input' : 'create-note-subject');
      this.alertScreenReader(this.isBatchFeature ? 'Create batch note form is open.' : 'Create note form is open');
    },
    saveAsTemplate() {
      this.showCreateTemplateModal = true;
      this.setFocusLockDisabled(true);
      this.putFocusNextTick('template-title-input');
    },
    showAlert(alert, seconds=3) {
      this.alert = alert;
      this.dismissAlertSeconds = seconds;
    },
    submitForm() {
      if (this.mode === 'editTemplate') {
        this.updateTemplate();
      } else {
        this.createNote();
      }
    },
    toggleShowCreateTemplateModal(show) {
      this.showCreateTemplateModal = show;
      this.setFocusLockDisabled(show);
    },
    updateTemplate() {
      this.setIsSaving(true);
      const newAttachments = this.filterList(this.model.attachments, a => !a.id);
      if (newAttachments.length) {
        // File upload might take time; alert will be overwritten when API call is done.
        this.showAlert('Updating template...', 60);
      }
      updateNoteTemplate(
        this.model.id,
        this.model.subject,
        this.model.body,
        this.model.topics,
        newAttachments,
        this.model.deleteAttachmentIds
      ).then(template => {
        this.setIsSaving(false);
        this.setModel({
          id: undefined,
          subject: template.subject,
          body: template.body,
          topics: template.topics,
          attachments: template.attachments,
          deleteAttachmentIds: []
        });
        this.setMode(this.isBatchFeature ? 'batch' : 'create');
        this.showAlert(`Template '${template.title}' updated`);
      });
    }
  }
}
</script>

<style scoped>
.batch-enter-active {
   -webkit-transition-duration: 0.3s;
   transition-duration: 0.3s;
   -webkit-transition-timing-function: ease-in;
   transition-timing-function: ease-in;
}
.batch-leave-active {
   -webkit-transition-duration: 0.3s;
   transition-duration: 0.5s;
   -webkit-transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
   transition-timing-function: cubic-bezier(0, 1, 0.5, 1);
}
.batch-enter-to, .batch-leave {
  max-height: 280px;
  overflow: hidden;
}
.batch-enter, .batch-leave-to {
  overflow: hidden;
  max-height: 0;
}
.create-note-container {
  display: block;
  position: fixed;
  z-index: 1;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: rgb(0,0,0);
  background-color: rgba(0,0,0,0.4);
}
.modal-content {
  background-color: #fff;
  margin: 140px auto auto auto;
  padding-bottom: 20px;
  border: 1px solid #888;
  width: 60%;
}
</style>
