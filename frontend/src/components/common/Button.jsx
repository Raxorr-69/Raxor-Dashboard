export default function Button({
  as: Component = "button",
  children,
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  type = "button",
  onClick,
  className = "",
  ...rest
}) {
  const classes = ["btn", `btn-${variant}`, `btn-${size}`, className]
    .filter(Boolean)
    .join(" ");

  // Only real <button> elements take type/disabled — an <a> rendered via
  // `as="a"` would choke on an unknown `disabled` attribute otherwise.
  const nativeButtonProps =
    Component === "button" ? { type, disabled: disabled || loading } : {};

  return (
    <Component className={classes} onClick={onClick} {...nativeButtonProps} {...rest}>
      {loading ? <span className="btn-spinner" aria-hidden="true" /> : null}
      {children}
    </Component>
  );
}
