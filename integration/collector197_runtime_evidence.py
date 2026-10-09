"""Mandatory source contract for independently verified runtime evidence.
No provider/default-ready implementation. Actual real-host provider is 197d.
This record does not itself grant owner permission; deployment must bind its
activation reference to authenticated owner evidence before creating it.
"""
from dataclasses import dataclass
from integration.collector197_coverage import catalog_fingerprint

class EvidenceRefused(ValueError):pass

@dataclass(frozen=True)
class RuntimeEvidence:
    catalog: str
    activation_reference: str
    host_reference: str
    observed_at: int
    expires_at: int
    available_memory_bytes: int
    wsgi_timeout_seconds: int
    bwrap_pid_namespace: bool
    nested_parser_bwrap: bool
    capacity_verified: bool

    def validate(self,now):
        if type(now)is not int or now<0 or self.catalog!=catalog_fingerprint():
            raise EvidenceRefused('Exact runtime evidence required')
        for value in (self.activation_reference,self.host_reference):
            if type(value)is not str or not 1<=len(value)<=200 or any(ord(c)<33 or ord(c)>126 for c in value):
                raise EvidenceRefused('Bounded source references required')
        if any(type(x)is not int for x in (self.observed_at,self.expires_at,self.available_memory_bytes,self.wsgi_timeout_seconds)):
            raise EvidenceRefused('Exact runtime limits required')
        if not 0<=self.observed_at<=now<self.expires_at<=self.observed_at+3600 or self.available_memory_bytes<1536*1024*1024 or self.wsgi_timeout_seconds<=120:
            raise EvidenceRefused('Runtime capacity or evidence expiry refused')
        if any(v is not True for v in (self.bwrap_pid_namespace,self.nested_parser_bwrap,self.capacity_verified)):
            raise EvidenceRefused('Verified runtime probes required')
        return dict.fromkeys(('runtime_bwrap','free_capacity','source_catalog','owner_activation'),True)


def evidence_provider(provider,clock):
    if not callable(provider):raise EvidenceRefused('Real evidence provider required')
    record=provider()
    if type(record)is not RuntimeEvidence:raise EvidenceRefused('Exact evidence record required')
    record.validate(clock())
    return record
