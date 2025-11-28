/**
 * useJobManager composable 測試
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'
import { useJobManager } from '@/composables/useJobManager'

// Mock API
vi.mock('@/services/api', () => ({
  api: {
    getJobs: vi.fn(),
    deleteJob: vi.fn(),
  },
}))

import { api } from '@/services/api'

// Helper component to use the composable
const TestComponent = defineComponent({
  setup() {
    return useJobManager()
  },
  template: '<div></div>',
})

describe('useJobManager', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()

    // Default mock response
    vi.mocked(api.getJobs).mockResolvedValue({
      jobs: [],
      processing: [],
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('selectJob', () => {
    it('should select a job by id', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [
          { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' },
        ],
        processing: [],
      })

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { selectJob, selectedJobId } = wrapper.vm as any
      selectJob('job-1')

      expect(selectedJobId).toBe('job-1')

      wrapper.unmount()
    })

    it('should set selectedJobId to null when null is passed', async () => {
      const wrapper = mount(TestComponent)
      await flushPromises()

      const { selectJob, selectedJobId } = wrapper.vm as any
      selectJob('job-1')
      selectJob(null)

      expect(selectedJobId).toBe(null)

      wrapper.unmount()
    })
  })

  describe('toggleDrawer', () => {
    it('should toggle drawer state', async () => {
      const wrapper = mount(TestComponent)
      await flushPromises()

      const { toggleDrawer, drawerOpen } = wrapper.vm as any
      const initialState = drawerOpen

      toggleDrawer()
      expect(wrapper.vm.drawerOpen).toBe(!initialState)

      toggleDrawer()
      expect(wrapper.vm.drawerOpen).toBe(initialState)

      wrapper.unmount()
    })
  })

  describe('setDrawerOpen', () => {
    it('should set drawer to open', async () => {
      const wrapper = mount(TestComponent)
      await flushPromises()

      const { setDrawerOpen } = wrapper.vm as any
      setDrawerOpen(true)

      expect(wrapper.vm.drawerOpen).toBe(true)

      wrapper.unmount()
    })

    it('should set drawer to closed', async () => {
      const wrapper = mount(TestComponent)
      await flushPromises()

      const { setDrawerOpen } = wrapper.vm as any
      setDrawerOpen(false)

      expect(wrapper.vm.drawerOpen).toBe(false)

      wrapper.unmount()
    })
  })

  describe('toggleJobSelection', () => {
    it('should add job to selection', async () => {
      const wrapper = mount(TestComponent)
      await flushPromises()

      const { toggleJobSelection, selectedJobIds } = wrapper.vm as any
      toggleJobSelection('job-1')

      expect(selectedJobIds.has('job-1')).toBe(true)

      wrapper.unmount()
    })

    it('should remove job from selection if already selected', async () => {
      const wrapper = mount(TestComponent)
      await flushPromises()

      const { toggleJobSelection, selectedJobIds } = wrapper.vm as any
      toggleJobSelection('job-1')
      toggleJobSelection('job-1')

      expect(selectedJobIds.has('job-1')).toBe(false)

      wrapper.unmount()
    })
  })

  describe('selectAllJobs', () => {
    it('should select all completed jobs', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [
          { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' },
          { id: 'job-2', source_title: 'Song 2', status: 'completed', source_type: 'upload', progress: 100, created_at: '' },
        ],
        processing: [],
      })

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { selectAllJobs, selectedJobIds } = wrapper.vm as any
      selectAllJobs()

      expect(selectedJobIds.has('job-1')).toBe(true)
      expect(selectedJobIds.has('job-2')).toBe(true)
      expect(selectedJobIds.size).toBe(2)

      wrapper.unmount()
    })
  })

  describe('deselectAllJobs', () => {
    it('should clear all selections', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [
          { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' },
        ],
        processing: [],
      })

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { selectAllJobs, deselectAllJobs, selectedJobIds } = wrapper.vm as any
      selectAllJobs()
      expect(selectedJobIds.size).toBe(1)

      deselectAllJobs()
      expect(selectedJobIds.size).toBe(0)

      wrapper.unmount()
    })
  })

  describe('deleteJob', () => {
    it('should delete job and remove from list', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [
          { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' },
        ],
        processing: [],
      })
      vi.mocked(api.deleteJob).mockResolvedValue(undefined)

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { deleteJob, completedJobs } = wrapper.vm as any
      expect(completedJobs.length).toBe(1)

      const result = await deleteJob('job-1')
      expect(result).toBe(true)
      expect(wrapper.vm.completedJobs.length).toBe(0)

      wrapper.unmount()
    })

    it('should return false on delete failure', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [
          { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' },
        ],
        processing: [],
      })
      vi.mocked(api.deleteJob).mockRejectedValue(new Error('Delete failed'))

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { deleteJob } = wrapper.vm as any
      const result = await deleteJob('job-1')
      expect(result).toBe(false)

      wrapper.unmount()
    })

    it('should clear selectedJobId if deleted job was selected', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [
          { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' },
        ],
        processing: [],
      })
      vi.mocked(api.deleteJob).mockResolvedValue(undefined)

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { selectJob, deleteJob, selectedJobId } = wrapper.vm as any
      selectJob('job-1')
      expect(selectedJobId).toBe('job-1')

      await deleteJob('job-1')
      expect(wrapper.vm.selectedJobId).toBe(null)

      wrapper.unmount()
    })
  })

  describe('computed properties', () => {
    it('hasProcessingJobs should be true when there are processing jobs', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [],
        processing: [
          { id: 'job-1', source_title: 'Processing', status: 'separating', source_type: 'youtube', progress: 50, created_at: '' },
        ],
      })

      const wrapper = mount(TestComponent)
      await flushPromises()

      expect(wrapper.vm.hasProcessingJobs).toBe(true)

      wrapper.unmount()
    })

    it('hasProcessingJobs should be false when there are no processing jobs', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [],
        processing: [],
      })

      const wrapper = mount(TestComponent)
      await flushPromises()

      expect(wrapper.vm.hasProcessingJobs).toBe(false)

      wrapper.unmount()
    })

    it('selectedJob should return the selected job object', async () => {
      const mockJob = { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' }
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [mockJob],
        processing: [],
      })

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { selectJob } = wrapper.vm as any
      selectJob('job-1')

      expect(wrapper.vm.selectedJob).toEqual(mockJob)

      wrapper.unmount()
    })

    it('selectedJobCount should return correct count', async () => {
      vi.mocked(api.getJobs).mockResolvedValue({
        jobs: [
          { id: 'job-1', source_title: 'Song 1', status: 'completed', source_type: 'youtube', progress: 100, created_at: '' },
          { id: 'job-2', source_title: 'Song 2', status: 'completed', source_type: 'upload', progress: 100, created_at: '' },
        ],
        processing: [],
      })

      const wrapper = mount(TestComponent)
      await flushPromises()

      const { toggleJobSelection } = wrapper.vm as any
      toggleJobSelection('job-1')
      toggleJobSelection('job-2')

      expect(wrapper.vm.selectedJobCount).toBe(2)

      wrapper.unmount()
    })
  })
})
