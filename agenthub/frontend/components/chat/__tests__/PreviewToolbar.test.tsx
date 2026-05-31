import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PreviewToolbar } from '../PreviewToolbar';

describe('PreviewToolbar', () => {
  it('renders title', () => {
    render(
      <PreviewToolbar
        title="Login Page"
        onCollapse={vi.fn()}
        onRefresh={vi.fn()}
        onCopy={vi.fn()}
      />
    );
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('calls onCollapse when collapse button is clicked', () => {
    const onCollapse = vi.fn();
    render(
      <PreviewToolbar
        title="Preview"
        onCollapse={onCollapse}
        onRefresh={vi.fn()}
        onCopy={vi.fn()}
      />
    );
    fireEvent.click(screen.getByLabelText('collapse'));
    expect(onCollapse).toHaveBeenCalled();
  });

  it('calls onRefresh when refresh button is clicked', () => {
    const onRefresh = vi.fn();
    render(
      <PreviewToolbar
        title="Preview"
        onCollapse={vi.fn()}
        onRefresh={onRefresh}
        onCopy={vi.fn()}
      />
    );
    fireEvent.click(screen.getByLabelText('refresh'));
    expect(onRefresh).toHaveBeenCalled();
  });

  it('calls onCopy when copy button is clicked', () => {
    const onCopy = vi.fn();
    render(
      <PreviewToolbar
        title="Preview"
        onCollapse={vi.fn()}
        onRefresh={vi.fn()}
        onCopy={onCopy}
      />
    );
    fireEvent.click(screen.getByLabelText('copy'));
    expect(onCopy).toHaveBeenCalled();
  });

  it('shows expand button when onExpand is provided', () => {
    render(
      <PreviewToolbar
        title="Preview"
        onCollapse={vi.fn()}
        onRefresh={vi.fn()}
        onCopy={vi.fn()}
        onExpand={vi.fn()}
      />
    );
    expect(screen.getByLabelText('expand')).toBeInTheDocument();
  });

  it('does not show expand button when onExpand is not provided', () => {
    render(
      <PreviewToolbar
        title="Preview"
        onCollapse={vi.fn()}
        onRefresh={vi.fn()}
        onCopy={vi.fn()}
      />
    );
    expect(screen.queryByLabelText('expand')).not.toBeInTheDocument();
  });

  it('applies rotation class when collapsed', () => {
    render(
      <PreviewToolbar
        title="Preview"
        isCollapsed={true}
        onCollapse={vi.fn()}
        onRefresh={vi.fn()}
        onCopy={vi.fn()}
      />
    );
    const collapseSvg = screen.getByLabelText('collapse').querySelector('svg');
    expect(collapseSvg).toHaveClass('-rotate-90');
  });
});
