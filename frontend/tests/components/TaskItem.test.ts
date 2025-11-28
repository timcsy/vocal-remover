/**
 * TaskItem 元件測試
 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskItem from '@/components/TaskItem.vue'
import type { ProcessingJob } from '@/services/api'

// Mock job data
const createMockJob = (overrides?: Partial<ProcessingJob>): ProcessingJob => ({
  id: 'test-job-456',
  source_title: 'Processing Song',
  source_type: 'youtube',
  status: 'separating',
  progress: 45,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

describe('TaskItem', () => {
  it('renders job title correctly', () => {
    const job = createMockJob({ source_title: 'My Processing Song' })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-title').text()).toBe('My Processing Song')
  })

  it('shows "處理中..." when source_title is empty', () => {
    const job = createMockJob({ source_title: '' })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-title').text()).toBe('處理中...')
  })

  it('displays progress percentage', () => {
    const job = createMockJob({ progress: 75 })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.progress-text').text()).toBe('75%')
  })

  it('sets progress bar width correctly', () => {
    const job = createMockJob({ progress: 60 })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    const progressFill = wrapper.find('.progress-fill')
    expect(progressFill.attributes('style')).toContain('width: 60%')
  })

  it('shows current_stage when available', () => {
    const job = createMockJob({ current_stage: '正在處理音軌...' })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-status').text()).toBe('正在處理音軌...')
  })

  it('shows status text for pending', () => {
    const job = createMockJob({ status: 'pending', current_stage: undefined })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-status').text()).toBe('等待中')
  })

  it('shows status text for downloading', () => {
    const job = createMockJob({ status: 'downloading', current_stage: undefined })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-status').text()).toBe('下載中')
  })

  it('shows status text for separating', () => {
    const job = createMockJob({ status: 'separating', current_stage: undefined })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-status').text()).toBe('分離人聲中')
  })

  it('shows status text for merging', () => {
    const job = createMockJob({ status: 'merging', current_stage: undefined })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-status').text()).toBe('影片擷取中')
  })

  it('shows status text for mixing', () => {
    const job = createMockJob({ status: 'mixing', current_stage: undefined })
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    expect(wrapper.find('.task-status').text()).toBe('混音中')
  })

  it('emits click event when clicked', async () => {
    const job = createMockJob()
    const wrapper = mount(TaskItem, {
      props: { job },
    })

    await wrapper.find('.task-item').trigger('click')

    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click')![0]).toEqual([job.id])
  })
})
