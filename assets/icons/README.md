# S3 Connector Icon Assets

This directory contains the icon assets for the OpenMetadata S3/MinIO Connector.

## 🎨 Icon Variants

### Standard Icon (64x64)
- **File**: `s3-connector-icon.svg`
- **Size**: 64x64 pixels
- **Usage**: Default connector icon in OpenMetadata UI
- **Format**: SVG with embedded styling

### Small Icon (32x32)
- **File**: `s3-connector-icon-small.svg`
- **Size**: 32x32 pixels
- **Usage**: Compact views, lists, navigation
- **Format**: Simplified SVG for clarity at small sizes

### Large Icon (128x128)
- **File**: `s3-connector-icon-large.svg`
- **Size**: 128x128 pixels
- **Usage**: Connector cards, detailed views, documentation
- **Format**: Enhanced SVG with gradients and effects

## 🎯 Design Elements

### Color Scheme
- **Primary**: `#FF9900` (Amazon Orange)
- **Secondary**: `#232F3E` (Amazon Dark Blue)
- **Accent**: `#FFFFFF` (White)
- **Metadata Indicators**: Various colors (`#4CAF50`, `#2196F3`, `#FF5722`, `#9C27B0`)

### Visual Components
1. **S3 Bucket**: Central cylinder representing S3 storage
2. **Data Flow Lines**: Dashed lines indicating data movement
3. **Metadata Indicators**: Colored dots representing different data types
4. **Gradient Background**: Professional finish with depth

## 📋 OpenMetadata Integration

### Connector Configuration
The icon can be referenced in OpenMetadata connector configurations:

```yaml
serviceType: "Database"
serviceName: "s3-connector"
sourceConfig:
  config:
    type: "DatabaseMetadata"
    # ... other configuration
connectionConfig:
  config:
    type: "S3"
    # Icon configuration
    icon: "assets/icons/s3-connector-icon.svg"
    smallIcon: "assets/icons/s3-connector-icon-small.svg"
    largeIcon: "assets/icons/s3-connector-icon-large.svg"
```

### Installation
1. Copy icon files to OpenMetadata's static assets directory
2. Update connector configuration to reference the icon paths
3. Restart OpenMetadata service to load new icons

## 🔧 Customization

### Modifying Colors
Update the SVG `fill` and `stroke` attributes to match your organization's branding:

```xml
<!-- Change primary color -->
<circle cx="32" cy="32" r="30" fill="#YOUR_PRIMARY_COLOR"/>

<!-- Change text color -->
<text fill="#YOUR_TEXT_COLOR">S3</text>
```

### Size Variants
Create additional size variants by scaling the viewBox and adjusting stroke widths proportionally.

## 📁 File Structure
```
assets/
└── icons/
    ├── s3-connector-icon.svg          # Standard (64x64)
    ├── s3-connector-icon-small.svg    # Small (32x32)
    ├── s3-connector-icon-large.svg    # Large (128x128)
    └── README.md                       # This file
```

## ✨ Usage Examples

### In Documentation
Reference the icons in markdown files:
```markdown
![S3 Connector](assets/icons/s3-connector-icon.svg)
```

### In Web Applications
Use as web assets:
```html
<img src="assets/icons/s3-connector-icon.svg" alt="S3 Connector" width="64" height="64">
```

### In OpenMetadata UI
The icons will automatically appear in:
- Connector selection screens
- Data source lists
- Service configuration pages
- Dashboard widgets

---

**🎨 Need custom icons?** Contact [mfonsau@talentys.eu](mailto:mfonsau@talentys.eu) for custom icon design services.
