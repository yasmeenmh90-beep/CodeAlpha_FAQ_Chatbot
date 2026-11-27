import { describe, it, expect } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import Playground from '../Playground'
import Operations from '../Operations'

describe('QueryMind AI Playground', () => {
  const render = () =>
    renderToStaticMarkup(
      createElement(Playground, {
        faqs: [
          { question: 'What is your refund policy?' }
        ]
      })
    )

  it('renders the playground workspace', () => {
    expect(render()).toContain('AI Playground')
  })

  it('renders retrieval configuration', () => {
    expect(render()).toContain('Experiment configuration')
  })

  it('renders similarity threshold control', () => {
    expect(render()).toContain('Similarity threshold')
  })

  it('renders ranked candidates', () => {
    expect(render()).toContain('Ranked candidates')
  })

  it('renders evaluation dataset controls', () => {
    expect(render()).toContain('Labeled evaluation dataset')
  })

  it('renders evaluation metrics', () => {
    expect(render()).toContain('Evaluation metrics')
  })
})

describe('QueryMind Operations', () => {
  it('renders System Monitor', () => {
    const html = renderToStaticMarkup(
      createElement(Operations, { mode: 'monitor' })
    )
    expect(html).toContain('System Monitor')
  })

  it('protects monitoring with administrator access', () => {
    const html = renderToStaticMarkup(
      createElement(Operations, { mode: 'monitor' })
    )
    expect(html).toContain('Unlock workspace')
    expect(html).not.toContain('Recent request log')
  })

  it('renders Support Tickets', () => {
    const html = renderToStaticMarkup(
      createElement(Operations, { mode: 'tickets' })
    )
    expect(html).toContain('Support Tickets')
  })

  it('renders ticket submission controls', () => {
    const html = renderToStaticMarkup(
      createElement(Operations, { mode: 'tickets' })
    )
    expect(html).toContain('Submit ticket')
    expect(html).toContain('Priority')
  })

  it('prefills an unresolved question', () => {
    const html = renderToStaticMarkup(
      createElement(Operations, {
        mode: 'tickets',
        initialQuestion: 'My order has not arrived'
      })
    )
    expect(html).toContain('My order has not arrived')
  })

  it('does not expose the locked ticket queue', () => {
    const html = renderToStaticMarkup(
      createElement(Operations, { mode: 'tickets' })
    )
    expect(html).not.toContain('Ticket queue')
  })
})
