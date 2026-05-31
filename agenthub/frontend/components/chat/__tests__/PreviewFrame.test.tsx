import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PreviewFrame } from '../PreviewFrame';

describe('PreviewFrame', () => {
  it('渲染 iframe', () => {
    render(
      <PreviewFrame htmlCode="<div>Hello</div>" height={400} />
    );
    const iframe = screen.getByTitle('网页预览') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();
    expect(iframe.getAttribute('sandbox')).toContain('allow-scripts');
  });

  it('处理 HTML 代码', () => {
    render(
      <PreviewFrame htmlCode="<div>Test</div>" height={300} />
    );
    const iframe = screen.getByTitle('网页预览') as HTMLIFrameElement;
    expect(iframe.srcdoc).toContain('viewport');
    expect(iframe.srcdoc).toContain('box-sizing');
  });

  it('设置正确的高度', () => {
    const { container } = render(
      <PreviewFrame htmlCode="<div>Hello</div>" height={500} />
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.style.height).toBe('500px');
  });

  it('处理空 htmlCode 输入', () => {
    render(<PreviewFrame htmlCode="" />);
    const iframe = screen.getByTitle('网页预览') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();
    expect(iframe.srcdoc).toBeTruthy();
  });

  it('默认高度为 400', () => {
    const { container } = render(
      <PreviewFrame htmlCode="<div>Hello</div>" />
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.style.height).toBe('400px');
  });
});
