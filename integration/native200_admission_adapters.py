"""Additive explicitly selected admission-aware pair; no runtime wiring."""
from integration.native200_adapters import NativeArchivedCollectorLedger,NativeArchivedProxyReceiptBudget
from integration.native200_admission_core import AdmissionArchiveCore
from integration.native200_admission_store import AdmissionStore
from integration.native200_transactions import NativeRefused
class _AdmissionSelection:
 def _init_native(self,core,family):
  if type(core)is not AdmissionArchiveCore or core.family!=family or core.enabled is not True or type(core.s)is not AdmissionStore:raise NativeRefused('Exact admission core selection')
  self.core=core
class AdmissionCollectorLedger(_AdmissionSelection,NativeArchivedCollectorLedger):pass
class AdmissionProxyReceiptBudget(_AdmissionSelection,NativeArchivedProxyReceiptBudget):pass
