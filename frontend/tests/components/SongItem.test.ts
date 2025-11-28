/**
 * SongItem 元件測試
 */
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SongItem from '@/components/SongItem.vue'
import type { CompletedJob } from '@/services/api'

// Mock job data
const createMockJob = (overrides?: Partial<CompletedJob>): CompletedJob => ({
  id: 'test-job-123',
  source_title: 'Test Song',
  source_type: 'youtube',
  status: 'completed',
  progress: 100,
  original_duration: 180,
  created_at: '2024-01-01T00:00:00Z',
  ...overrides,
})

describe('SongItem', () => {
  it('renders job title correctly', () => {
    const job = createMockJob({ source_title: 'My Test Song' })
    const wrapper = mount(SongItem, {
      props: { job },
    })

    expect(wrapper.find('.song-title').text()).toBe('My Test Song')
  })

  it('shows "未命名" when source_title is empty', () => {
    const job = createMockJob({ source_title: '' })
    const wrapper = mount(SongItem, {
      props: { job },
    })

    expect(wrapper.find('.song-title').text()).toBe('未命名')
  })

  it('formats duration correctly', () => {
    const job = createMockJob({ original_duration: 185 }) // 3:05
    const wrapper = mount(SongItem, {
      props: { job },
    })

    expect(wrapper.find('.duration').text()).toBe('3:05')
  })

  it('shows YouTube source type', () => {
    const job = createMockJob({ source_type: 'youtube' })
    const wrapper = mount(SongItem, {
      props: { job },
    })

    expect(wrapper.find('.source-type').text()).toBe('YouTube')
  })

  it('shows upload source type', () => {
    const job = createMockJob({ source_type: 'upload' })
    const wrapper = mount(SongItem, {
      props: { job },
    })

    expect(wrapper.find('.source-type').text()).toBe('上傳')
  })

  it('emits select event when clicked', async () => {
    const job = createMockJob()
    const wrapper = mount(SongItem, {
      props: { job },
    })

    await wrapper.find('.song-item').trigger('click')

    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')![0]).toEqual([job.id])
  })

  it('emits toggle event when checkbox is clicked', async () => {
    const job = createMockJob()
    const wrapper = mount(SongItem, {
      props: { job },
    })

    await wrapper.find('.song-checkbox').trigger('click')

    expect(wrapper.emitted('toggle')).toBeTruthy()
    expect(wrapper.emitted('toggle')![0]).toEqual([job.id])
  })

  it('emits delete event when delete button is clicked', async () => {
    const job = createMockJob()
    const wrapper = mount(SongItem, {
      props: { job, showDelete: true },
    })

    await wrapper.find('.delete-btn').trigger('click')

    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')![0]).toEqual([job.id])
  })

  it('does not show delete button when showDelete is false', () => {
    const job = createMockJob()
    const wrapper = mount(SongItem, {
      props: { job, showDelete: false },
    })

    expect(wrapper.find('.delete-btn').exists()).toBe(false)
  })

  it('applies selected class when isSelected is true', () => {
    const job = createMockJob()
    const wrapper = mount(SongItem, {
      props: { job, isSelected: true },
    })

    expect(wrapper.find('.song-item').classes()).toContain('selected')
  })

  it('applies checked class when isChecked is true', () => {
    const job = createMockJob()
    const wrapper = mount(SongItem, {
      props: { job, isChecked: true },
    })

    expect(wrapper.find('.song-item').classes()).toContain('checked')
  })

  it('checkbox reflects isChecked prop', () => {
    const job = createMockJob()
    const wrapper = mount(SongItem, {
      props: { job, isChecked: true },
    })

    const checkbox = wrapper.find('.song-checkbox').element as HTMLInputElement
    expect(checkbox.checked).toBe(true)
  })
})
