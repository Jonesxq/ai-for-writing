import request from './request'

export const initNovel = data => request.post('/novel/init', data)
export const nextChapter = data => request.post('/novel/next_chapter', data)
export const getStatus = novelId => request.get(`/novel/status/${novelId}`)
export const getNovelList = () =>request.get('/novel/list')
export const exportNovel = novelId =>
  request.get(`/novel/export/${novelId}`, { responseType: 'blob' })
