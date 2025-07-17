# 🎨 S3 Connector Icon Integration Guide

This guide explains how to integrate the custom S3 connector icon into OpenMetadata for a professional, branded connector experience.

## 🎯 Overview

The S3 connector now includes dedicated icons that provide visual identity within the OpenMetadata interface. The icons are professionally designed to represent S3/MinIO storage with clear metadata indicators.

## 📁 Icon Assets

### Available Icon Variants

| Icon | Size | Usage | File |
|------|------|-------|------|
| **Standard** | 64x64px | Default connector views | `s3-connector-icon.svg` |
| **Small** | 32x32px | Lists, navigation, compact views | `s3-connector-icon-small.svg` |
| **Large** | 128x128px | Cards, featured displays | `s3-connector-icon-large.svg` |

### Design Features
- **AWS-inspired colors**: Orange (#FF9900) and dark blue (#232F3E)
- **S3 bucket representation**: Cylindrical storage container
- **Metadata indicators**: Colored dots representing different data types
- **Data flow lines**: Visual indication of data movement
- **Professional gradients**: Enhanced visual appeal for larger sizes

## 🔧 OpenMetadata Integration

### Method 1: Direct Configuration

Add icon references to your connector configuration:

```yaml
source:
  type: "s3"
  serviceName: "s3-connector"
  
  # Icon configuration
  serviceIcon:
    default: "assets/icons/s3-connector-icon.svg"
    small: "assets/icons/s3-connector-icon-small.svg"
    large: "assets/icons/s3-connector-icon-large.svg"
  
  # ... rest of configuration
```

### Method 2: Connector Manifest

Use the provided `connector-manifest.json`:

```json
{
  "name": "s3-connector",
  "displayName": "S3/MinIO Connector",
  "icon": {
    "default": "assets/icons/s3-connector-icon.svg",
    "small": "assets/icons/s3-connector-icon-small.svg",
    "large": "assets/icons/s3-connector-icon-large.svg"
  }
}
```

### Method 3: Package Integration

The icons are automatically included when installing the connector package:

```bash
pip install openmetadata-s3-connector
```

## 🚀 Installation Steps

### Step 1: Copy Icon Assets

```bash
# Copy icons to OpenMetadata static assets directory
cp -r assets/icons/ /path/to/openmetadata/static/assets/connectors/s3/

# Or use the full package installation
pip install -e .
```

### Step 2: Update OpenMetadata Configuration

Edit your OpenMetadata server configuration to recognize the new connector:

```yaml
# openmetadata.yaml
connectorRegistry:
  - name: "s3-connector"
    type: "Database" 
    serviceType: "S3"
    iconPath: "assets/connectors/s3/s3-connector-icon.svg"
    manifest: "assets/connectors/s3/connector-manifest.json"
```

### Step 3: Restart OpenMetadata

```bash
# Restart OpenMetadata service
systemctl restart openmetadata

# Or for Docker deployments
docker-compose restart openmetadata-server
```

## 🖥️ UI Appearance

### Connector Selection Screen
The icon will appear when selecting data sources:
- Large icon (128x128) for featured connector cards
- Standard icon (64x64) for grid view
- Small icon (32x32) for list view

### Service Configuration
During connector setup:
- Icon displayed in configuration wizard header
- Visual confirmation of connector type
- Consistent branding throughout setup process

### Data Catalog
In the data catalog interface:
- Service icons in navigation
- Table source indicators
- Lineage diagram representations

## 🎨 Customization

### Brand Colors

To match your organization's branding, modify the SVG fill colors:

```xml
<!-- Primary background -->
<circle cx="32" cy="32" r="30" fill="#YOUR_PRIMARY_COLOR"/>

<!-- Secondary elements -->
<path fill="#YOUR_SECONDARY_COLOR"/>

<!-- Text color -->
<text fill="#YOUR_TEXT_COLOR">S3</text>
```

### Custom Variants

Create additional icon variants for specific environments:

```bash
# Development environment (green accent)
cp s3-connector-icon.svg s3-connector-icon-dev.svg
# Modify colors for development

# Production environment (red accent)  
cp s3-connector-icon.svg s3-connector-icon-prod.svg
# Modify colors for production
```

## 🔍 Troubleshooting

### Icon Not Appearing

1. **Check file paths**:
   ```bash
   ls -la assets/icons/
   # Verify all icon files exist
   ```

2. **Verify permissions**:
   ```bash
   chmod 644 assets/icons/*.svg
   # Ensure files are readable
   ```

3. **Clear browser cache**:
   - Hard refresh (Ctrl+F5)
   - Clear OpenMetadata cache

### Incorrect Icon Size

1. **Check viewport dimensions** in SVG files
2. **Verify CSS sizing** in OpenMetadata configuration
3. **Test different browsers** for consistency

### Icon Quality Issues

1. **Use vector SVG format** for scalability
2. **Optimize SVG files** for web delivery
3. **Test at different zoom levels**

## 📊 Icon Usage Statistics

Track icon effectiveness in OpenMetadata:

```yaml
# Analytics configuration
analytics:
  trackIconUsage: true
  iconMetrics:
    - connector_selection_rate
    - visual_recognition_time
    - user_preference_score
```

## 🎯 Best Practices

### File Organization
```
assets/
├── icons/
│   ├── s3-connector-icon.svg          # Standard (64x64)
│   ├── s3-connector-icon-small.svg    # Small (32x32)  
│   ├── s3-connector-icon-large.svg    # Large (128x128)
│   └── README.md                       # Documentation
├── connector-manifest.json             # Connector metadata
└── themes/                             # Optional themes
    ├── dark-theme/
    └── light-theme/
```

### Performance Optimization
- Use SVG format for vector scalability
- Minimize file sizes (typically < 5KB)
- Optimize for web delivery
- Consider dark/light theme variants

### Accessibility
- Provide alt text descriptions
- Ensure sufficient color contrast
- Test with screen readers
- Support high contrast modes

## 📚 Related Documentation

- [OpenMetadata Connector Development](https://docs.open-metadata.org/connectors)
- [Custom Connector Icons](https://docs.open-metadata.org/developers/contribute/build-a-connector)
- [UI Customization Guide](https://docs.open-metadata.org/deployment/customize-ui)

## 🤝 Contributing

To contribute icon improvements:

1. **Fork the repository**
2. **Create icon variants** following the design guidelines
3. **Test in OpenMetadata UI** 
4. **Submit pull request** with screenshots

---

**🎨 Icon Design**: Professional S3 connector icons for enhanced user experience  
**📧 Support**: [mfonsau@talentys.eu](mailto:mfonsau@talentys.eu)  
**🔗 Repository**: [S3 Connector Playbook](https://github.com/Monsau/S3connectorplaybook)
