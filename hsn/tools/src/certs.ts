// Certificate & compliance rules for Indian import/export, by HS chapter family.
// Curated from official instruments (named per rule). Family-level: the exact 8-digit
// line's policy condition lives in DGFT ITC-HS Schedule-1 - the panel says so.
// shape: [chapter ranges, agency short, requirement, instrument]
export const CERT_RULES = [
  { from: 1, to: 1, who: 'DAHD', what: 'Sanitary import permit before shipping live animals', law: 'Livestock Importation Act 1898', side: 'in' },
  { from: 2, to: 5, who: 'DAHD', what: 'Sanitary import permit for animal products (meat, dairy, eggs, honey)', law: 'Livestock Importation Act 1898', side: 'in' },
  { from: 6, to: 14, who: 'Plant Quarantine', what: 'Phytosanitary certificate from the exporter side + import permit for planting material; inspection on arrival', law: 'Plant Quarantine (Regulation of Import into India) Order 2003', side: 'in' },
  { from: 2, to: 21, who: 'FSSAI', what: 'Food import clearance - FSSAI license and per-consignment testing at the port', law: 'FSS Act 2006 + Food Safety and Standards (Import) Regulations 2017', side: 'in' },
  { from: 29, to: 30, who: 'CDSCO', what: 'Drug import registration and import license (bulk drugs and formulations)', law: 'Drugs and Cosmetics Act 1940 + Rules 1945', side: 'in' },
  { from: 28, to: 38, who: 'BIS / line ministry', what: 'Many chemicals are under Quality Control Orders - BIS licence needed before import if the exact line is covered', law: 'BIS Act 2016 QCOs; DGFT ITC-HS Schedule-1 Appendix-III', side: 'in' },
  { from: 72, to: 83, who: 'BIS', what: 'Steel, copper, aluminium and many metal products are under mandatory BIS Quality Control Orders', law: 'BIS Act 2016 QCOs; DGFT Appendix-III', side: 'in' },
  { from: 84, to: 85, who: 'BIS / WPC', what: 'Many electronics need BIS registration (CRS); anything with wireless/RF needs WPC equipment type approval', law: 'BIS CRS QCOs; Indian Wireless Telegraphy Act 1933', side: 'in' },
  { from: 95, to: 95, who: 'BIS', what: 'Toys must carry BIS certification', law: 'Toys (Quality Control) Order 2020', side: 'in' },
  { from: 2, to: 21, who: 'Export Inspection Council / APEDA', what: 'Food and agri exports: health certificate from EIC/EIA and APEDA registration where the destination asks', law: 'Export (Quality Control and Inspection) Act 1963', side: 'out' },
  { from: 6, to: 14, who: 'Plant Quarantine (India)', what: 'Agri exports: Indian phytosanitary certificate issued before shipment when the destination requires it', law: 'Plant Quarantine Order 2003 + destination rules', side: 'out' },
  { from: 1, to: 5, who: 'DAHD (India)', what: 'Animal-product exports: veterinary health certificate matching the destination country template', law: 'Destination-country SPS requirements', side: 'out' }
];
export const CERT_SRC = 'Rules summarised from the named official instruments; the exact 8-digit line policy condition is in DGFT ITC-HS Schedule-1 (dgft.gov.in) - verify there before shipping.';
