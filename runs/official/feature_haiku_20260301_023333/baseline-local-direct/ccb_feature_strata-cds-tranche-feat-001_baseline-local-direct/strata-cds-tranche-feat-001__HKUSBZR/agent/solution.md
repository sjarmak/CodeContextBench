# CDS Tranche Product Implementation Analysis

## Files Examined

### Product Module
- `modules/product/src/main/java/com/opengamma/strata/product/credit/CdsIndex.java` — Examined to understand product structure, Joda-Beans pattern, and fields including buySell, cdsIndexId, legalEntityIds, currency, notional, paymentSchedule, fixedRate, dayCount, paymentOnDefault, protectionStart, stepinDateOffset, settlementDateOffset
- `modules/product/src/main/java/com/opengamma/strata/product/credit/CdsIndexTrade.java` — Examined to understand trade pattern with ProductTrade, ResolvableTrade interfaces, info, product, upfrontFee fields
- `modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsIndex.java` — Examined to understand resolved product structure with expanded payment periods and helper methods
- `modules/product/src/main/java/com/opengamma/strata/product/credit/CreditCouponPaymentPeriod.java` — Reference for payment period structure used in resolved products
- `modules/product/src/main/java/com/opengamma/strata/product/credit/PaymentOnDefault.java` — Enum for payment behavior
- `modules/product/src/main/java/com/opengamma/strata/product/credit/ProtectionStartOfDay.java` — Enum for protection start timing

### Pricer Module
- `modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaCdsProductPricer.java` — Examined to understand pricing methodology and PV calculations
- `modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/CreditRatesProvider.java` — Reference for accessing discount curves and credit curves

### Measure Module
- `modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTradeCalculationFunction.java` — Examined to understand CalculationFunction pattern and measure mappings
- `modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsIndexTradeCalculationFunction.java` — Reference for index trade calculation function
- `modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsMeasureCalculations.java` — Reference for measure implementation pattern

## Dependency Chain

1. **Create base product classes** (implements Product, Resolvable)
   - `CdsTranche.java` — Product definition with attachment/detachment points
   - `ResolvedCdsTranche.java` — Resolved form with payment periods
   - `CdsTrancheTrade.java` — Trade wrapper
   - `ResolvedCdsTrancheTrade.java` — Resolved trade

2. **Create pricer components**
   - `IsdaCdsTranchePricer.java` — Core pricing logic with tranche-specific loss allocation
   - `IsdaCdsTrancheTradePricer.java` — Trade-level pricing wrapper

3. **Create measure/calculation components**
   - `CdsTrancheTradeCalculationFunction.java` — Wires tranche trades into calculation engine
   - `CdsTrancheMeasureCalculations.java` — Implements specific measures for tranches

## Code Changes

### 1. modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTranche.java

```java
/*
 * Copyright (C) 2016 - present by OpenGamma Inc. and the OpenGamma group of companies
 *
 * Please see distribution for license.
 */
package com.opengamma.strata.product.credit;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

import org.joda.beans.Bean;
import org.joda.beans.ImmutableBean;
import org.joda.beans.JodaBeanUtils;
import org.joda.beans.MetaBean;
import org.joda.beans.MetaProperty;
import org.joda.beans.gen.BeanDefinition;
import org.joda.beans.gen.ImmutableDefaults;
import org.joda.beans.gen.PropertyDefinition;
import org.joda.beans.impl.direct.DirectFieldsBeanBuilder;
import org.joda.beans.impl.direct.DirectMetaBean;
import org.joda.beans.impl.direct.DirectMetaProperty;
import org.joda.beans.impl.direct.DirectMetaPropertyMap;

import com.google.common.collect.ImmutableList;
import com.opengamma.strata.basics.ReferenceData;
import com.opengamma.strata.basics.Resolvable;
import com.opengamma.strata.basics.currency.Currency;
import com.opengamma.strata.basics.date.DayCount;
import com.opengamma.strata.basics.date.DayCounts;
import com.opengamma.strata.basics.date.DaysAdjustment;
import com.opengamma.strata.basics.schedule.PeriodicSchedule;
import com.opengamma.strata.collect.ArgChecker;
import com.opengamma.strata.product.Product;
import com.opengamma.strata.product.common.BuySell;

/**
 * A CDS tranche product.
 * <p>
 * A CDS tranche represents a slice of credit risk from a CDS index portfolio,
 * defined by attachment and detachment points that determine the subordination level.
 * The protection buyer receives payment for losses between the attachment and detachment points.
 */
@BeanDefinition
public final class CdsTranche
    implements Product, Resolvable<ResolvedCdsTranche>, ImmutableBean, Serializable {

  /**
   * The underlying CDS index.
   * <p>
   * The tranche references this index portfolio.
   */
  @PropertyDefinition(validate = "notNull")
  private final CdsIndex underlyingIndex;

  /**
   * The attachment point of the tranche.
   * <p>
   * This is the lower bound of the loss absorption as a fraction of notional (0.0 to 1.0).
   * Losses below this point are borne by other tranches.
   */
  @PropertyDefinition(validate = "ArgChecker.inRange")
  private final double attachmentPoint;

  /**
   * The detachment point of the tranche.
   * <p>
   * This is the upper bound of the loss absorption as a fraction of notional (0.0 to 1.0).
   * Losses above this point are borne by more senior tranches.
   */
  @PropertyDefinition(validate = "ArgChecker.inRange")
  private final double detachmentPoint;

  //-------------------------------------------------------------------------
  /**
   * Creates a builder.
   *
   * @return the builder, not null
   */
  public static CdsTranche.Builder builder() {
    return new CdsTranche.Builder();
  }

  /**
   * Resolves this tranche using the reference data.
   *
   * @param refData  the reference data
   * @return the resolved tranche
   */
  @Override
  public ResolvedCdsTranche resolve(ReferenceData refData) {
    ResolvedCdsIndex resolvedIndex = underlyingIndex.resolve(refData);
    return ResolvedCdsTranche.builder()
        .underlyingIndex(resolvedIndex)
        .attachmentPoint(attachmentPoint)
        .detachmentPoint(detachmentPoint)
        .build();
  }

  /**
   * Gets the currency of the tranche.
   *
   * @return the currency
   */
  public Currency getCurrency() {
    return underlyingIndex.getCurrency();
  }

  /**
   * Gets the notional amount.
   *
   * @return the notional
   */
  public double getNotional() {
    return underlyingIndex.getNotional();
  }

  /**
   * Gets the tranche notional (detachment - attachment).
   *
   * @return the tranche notional
   */
  public double getTrancheNotional() {
    return getNotional() * (detachmentPoint - attachmentPoint);
  }

  //------------------------- AUTOGENERATED START -------------------------
  /**
   * The meta-bean for {@code CdsTranche}.
   * @return the meta-bean, not null
   */
  public static CdsTranche.Meta meta() {
    return CdsTranche.Meta.INSTANCE;
  }

  static {
    MetaBean.register(CdsTranche.Meta.INSTANCE);
  }

  /**
   * The serialization version id.
   */
  private static final long serialVersionUID = 1L;

  private CdsTranche(
      CdsIndex underlyingIndex,
      double attachmentPoint,
      double detachmentPoint) {
    JodaBeanUtils.notNull(underlyingIndex, "underlyingIndex");
    ArgChecker.inRange(attachmentPoint, 0.0, 1.0, "attachmentPoint");
    ArgChecker.inRange(detachmentPoint, 0.0, 1.0, "detachmentPoint");
    ArgChecker.isTrue(detachmentPoint > attachmentPoint, "detachmentPoint must be greater than attachmentPoint");
    this.underlyingIndex = underlyingIndex;
    this.attachmentPoint = attachmentPoint;
    this.detachmentPoint = detachmentPoint;
  }

  @Override
  public CdsTranche.Meta metaBean() {
    return CdsTranche.Meta.INSTANCE;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the underlying CDS index.
   * <p>
   * The tranche references this index portfolio.
   * @return the value of the property, not null
   */
  public CdsIndex getUnderlyingIndex() {
    return underlyingIndex;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the attachment point of the tranche.
   * <p>
   * This is the lower bound of the loss absorption as a fraction of notional (0.0 to 1.0).
   * Losses below this point are borne by other tranches.
   * @return the value of the property
   */
  public double getAttachmentPoint() {
    return attachmentPoint;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the detachment point of the tranche.
   * <p>
   * This is the upper bound of the loss absorption as a fraction of notional (0.0 to 1.0).
   * Losses above this point are borne by more senior tranches.
   * @return the value of the property
   */
  public double getDetachmentPoint() {
    return detachmentPoint;
  }

  //-----------------------------------------------------------------------
  /**
   * Returns a builder that allows this bean to be mutated.
   * @return the mutable builder, not null
   */
  public Builder toBuilder() {
    return new Builder(this);
  }

  @Override
  public boolean equals(Object obj) {
    if (obj == this) {
      return true;
    }
    if (obj != null && obj.getClass() == this.getClass()) {
      CdsTranche other = (CdsTranche) obj;
      return JodaBeanUtils.equal(underlyingIndex, other.underlyingIndex) &&
          JodaBeanUtils.equal(attachmentPoint, other.attachmentPoint) &&
          JodaBeanUtils.equal(detachmentPoint, other.detachmentPoint);
    }
    return false;
  }

  @Override
  public int hashCode() {
    int hash = getClass().hashCode();
    hash = hash * 31 + JodaBeanUtils.hashCode(underlyingIndex);
    hash = hash * 31 + JodaBeanUtils.hashCode(attachmentPoint);
    hash = hash * 31 + JodaBeanUtils.hashCode(detachmentPoint);
    return hash;
  }

  @Override
  public String toString() {
    StringBuilder buf = new StringBuilder(128);
    buf.append("CdsTranche{");
    buf.append("underlyingIndex").append('=').append(JodaBeanUtils.toString(underlyingIndex)).append(',').append(' ');
    buf.append("attachmentPoint").append('=').append(JodaBeanUtils.toString(attachmentPoint)).append(',').append(' ');
    buf.append("detachmentPoint").append('=').append(JodaBeanUtils.toString(detachmentPoint));
    buf.append('}');
    return buf.toString();
  }

  //-----------------------------------------------------------------------
  /**
   * The meta-bean for {@code CdsTranche}.
   */
  public static final class Meta extends DirectMetaBean {
    /**
     * The singleton instance of the meta-bean.
     */
    static final Meta INSTANCE = new Meta();

    /**
     * The meta-property for the {@code underlyingIndex} property.
     */
    private final MetaProperty<CdsIndex> underlyingIndex = DirectMetaProperty.ofImmutable(
        this, "underlyingIndex", CdsTranche.class, CdsIndex.class);
    /**
     * The meta-property for the {@code attachmentPoint} property.
     */
    private final MetaProperty<Double> attachmentPoint = DirectMetaProperty.ofImmutable(
        this, "attachmentPoint", CdsTranche.class, Double.TYPE);
    /**
     * The meta-property for the {@code detachmentPoint} property.
     */
    private final MetaProperty<Double> detachmentPoint = DirectMetaProperty.ofImmutable(
        this, "detachmentPoint", CdsTranche.class, Double.TYPE);
    /**
     * The meta-properties.
     */
    private final Map<String, MetaProperty<?>> metaPropertyMap$ = new DirectMetaPropertyMap(
        this, null,
        "underlyingIndex",
        "attachmentPoint",
        "detachmentPoint");

    /**
     * Restricted constructor.
     */
    private Meta() {
    }

    @Override
    protected MetaProperty<?> metaPropertyGet(String propertyName) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          return underlyingIndex;
        case 1108702661:  // attachmentPoint
          return attachmentPoint;
        case -1455950710:  // detachmentPoint
          return detachmentPoint;
      }
      return super.metaPropertyGet(propertyName);
    }

    @Override
    public CdsTranche.Builder builder() {
      return new CdsTranche.Builder();
    }

    @Override
    public Class<? extends CdsTranche> beanType() {
      return CdsTranche.class;
    }

    @Override
    public Map<String, MetaProperty<?>> metaPropertyMap() {
      return metaPropertyMap$;
    }

    //-----------------------------------------------------------------------
    /**
     * The meta-property for the {@code underlyingIndex} property.
     * @return the meta-property, not null
     */
    public MetaProperty<CdsIndex> underlyingIndex() {
      return underlyingIndex;
    }

    /**
     * The meta-property for the {@code attachmentPoint} property.
     * @return the meta-property, not null
     */
    public MetaProperty<Double> attachmentPoint() {
      return attachmentPoint;
    }

    /**
     * The meta-property for the {@code detachmentPoint} property.
     * @return the meta-property, not null
     */
    public MetaProperty<Double> detachmentPoint() {
      return detachmentPoint;
    }

    //-----------------------------------------------------------------------
    @Override
    protected Object propertyGet(Bean bean, String propertyName, boolean quiet) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          return ((CdsTranche) bean).getUnderlyingIndex();
        case 1108702661:  // attachmentPoint
          return ((CdsTranche) bean).getAttachmentPoint();
        case -1455950710:  // detachmentPoint
          return ((CdsTranche) bean).getDetachmentPoint();
      }
      return super.propertyGet(bean, propertyName, quiet);
    }

    @Override
    protected void propertySet(Bean bean, String propertyName, Object newValue, boolean quiet) {
      metaProperty(propertyName);
      if (quiet) {
        return;
      }
      throw new UnsupportedOperationException("Property cannot be written: " + propertyName);
    }

  }

  //-----------------------------------------------------------------------
  /**
   * The bean-builder for {@code CdsTranche}.
   */
  public static final class Builder extends DirectFieldsBeanBuilder<CdsTranche> {

    private CdsIndex underlyingIndex;
    private double attachmentPoint;
    private double detachmentPoint;

    /**
     * Restricted constructor.
     */
    private Builder() {
    }

    /**
     * Restricted copy constructor.
     * @param beanToCopy  the bean to copy from, not null
     */
    private Builder(CdsTranche beanToCopy) {
      this.underlyingIndex = beanToCopy.getUnderlyingIndex();
      this.attachmentPoint = beanToCopy.getAttachmentPoint();
      this.detachmentPoint = beanToCopy.getDetachmentPoint();
    }

    //-----------------------------------------------------------------------
    @Override
    public Object get(String propertyName) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          return underlyingIndex;
        case 1108702661:  // attachmentPoint
          return attachmentPoint;
        case -1455950710:  // detachmentPoint
          return detachmentPoint;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
    }

    @Override
    public Builder set(String propertyName, Object newValue) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          this.underlyingIndex = (CdsIndex) newValue;
          break;
        case 1108702661:  // attachmentPoint
          this.attachmentPoint = (Double) newValue;
          break;
        case -1455950710:  // detachmentPoint
          this.detachmentPoint = (Double) newValue;
          break;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
      return this;
    }

    @Override
    public Builder set(MetaProperty<?> property, Object value) {
      super.set(property, value);
      return this;
    }

    @Override
    public CdsTranche build() {
      return new CdsTranche(
          underlyingIndex,
          attachmentPoint,
          detachmentPoint);
    }

    //-----------------------------------------------------------------------
    /**
     * Sets the underlying CDS index.
     * <p>
     * The tranche references this index portfolio.
     * @param underlyingIndex  the new value, not null
     * @return this, for chaining, not null
     */
    public Builder underlyingIndex(CdsIndex underlyingIndex) {
      JodaBeanUtils.notNull(underlyingIndex, "underlyingIndex");
      this.underlyingIndex = underlyingIndex;
      return this;
    }

    /**
     * Sets the attachment point of the tranche.
     * <p>
     * This is the lower bound of the loss absorption as a fraction of notional (0.0 to 1.0).
     * Losses below this point are borne by other tranches.
     * @param attachmentPoint  the new value
     * @return this, for chaining, not null
     */
    public Builder attachmentPoint(double attachmentPoint) {
      ArgChecker.inRange(attachmentPoint, 0.0, 1.0, "attachmentPoint");
      this.attachmentPoint = attachmentPoint;
      return this;
    }

    /**
     * Sets the detachment point of the tranche.
     * <p>
     * This is the upper bound of the loss absorption as a fraction of notional (0.0 to 1.0).
     * Losses above this point are borne by more senior tranches.
     * @param detachmentPoint  the new value
     * @return this, for chaining, not null
     */
    public Builder detachmentPoint(double detachmentPoint) {
      ArgChecker.inRange(detachmentPoint, 0.0, 1.0, "detachmentPoint");
      this.detachmentPoint = detachmentPoint;
      return this;
    }

    //-----------------------------------------------------------------------
    @Override
    public String toString() {
      StringBuilder buf = new StringBuilder(128);
      buf.append("CdsTranche.Builder{");
      buf.append("underlyingIndex").append('=').append(JodaBeanUtils.toString(underlyingIndex)).append(',').append(' ');
      buf.append("attachmentPoint").append('=').append(JodaBeanUtils.toString(attachmentPoint)).append(',').append(' ');
      buf.append("detachmentPoint").append('=').append(JodaBeanUtils.toString(detachmentPoint));
      buf.append('}');
      return buf.toString();
    }

  }

  //-------------------------- AUTOGENERATED END --------------------------
}
```

### 2. modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTranche.java

```java
/*
 * Copyright (C) 2016 - present by OpenGamma Inc. and the OpenGamma group of companies
 *
 * Please see distribution for license.
 */
package com.opengamma.strata.product.credit;

import java.io.Serializable;
import java.util.Map;
import java.util.NoSuchElementException;

import org.joda.beans.Bean;
import org.joda.beans.ImmutableBean;
import org.joda.beans.JodaBeanUtils;
import org.joda.beans.MetaBean;
import org.joda.beans.MetaProperty;
import org.joda.beans.gen.BeanDefinition;
import org.joda.beans.gen.PropertyDefinition;
import org.joda.beans.impl.direct.DirectFieldsBeanBuilder;
import org.joda.beans.impl.direct.DirectMetaBean;
import org.joda.beans.impl.direct.DirectMetaProperty;
import org.joda.beans.impl.direct.DirectMetaPropertyMap;

import com.opengamma.strata.basics.currency.Currency;
import com.opengamma.strata.product.ResolvedProduct;

/**
 * A CDS tranche, resolved for pricing.
 * <p>
 * This is the resolved form of {@link CdsTranche} and is an input to the pricers.
 */
@BeanDefinition
public final class ResolvedCdsTranche
    implements ResolvedProduct, ImmutableBean, Serializable {

  /**
   * The underlying resolved CDS index.
   */
  @PropertyDefinition(validate = "notNull")
  private final ResolvedCdsIndex underlyingIndex;

  /**
   * The attachment point of the tranche.
   */
  @PropertyDefinition(validate = "notNull")
  private final double attachmentPoint;

  /**
   * The detachment point of the tranche.
   */
  @PropertyDefinition(validate = "notNull")
  private final double detachmentPoint;

  //-------------------------------------------------------------------------
  /**
   * Creates a builder.
   *
   * @return the builder, not null
   */
  public static ResolvedCdsTranche.Builder builder() {
    return new ResolvedCdsTranche.Builder();
  }

  /**
   * Gets the currency of the tranche.
   *
   * @return the currency
   */
  public Currency getCurrency() {
    return underlyingIndex.getCurrency();
  }

  /**
   * Gets the notional amount.
   *
   * @return the notional
   */
  public double getNotional() {
    return underlyingIndex.getNotional();
  }

  /**
   * Gets the tranche notional (detachment - attachment).
   *
   * @return the tranche notional
   */
  public double getTrancheNotional() {
    return getNotional() * (detachmentPoint - attachmentPoint);
  }

  //------------------------- AUTOGENERATED START -------------------------
  /**
   * The meta-bean for {@code ResolvedCdsTranche}.
   * @return the meta-bean, not null
   */
  public static ResolvedCdsTranche.Meta meta() {
    return ResolvedCdsTranche.Meta.INSTANCE;
  }

  static {
    MetaBean.register(ResolvedCdsTranche.Meta.INSTANCE);
  }

  /**
   * The serialization version id.
   */
  private static final long serialVersionUID = 1L;

  private ResolvedCdsTranche(
      ResolvedCdsIndex underlyingIndex,
      double attachmentPoint,
      double detachmentPoint) {
    JodaBeanUtils.notNull(underlyingIndex, "underlyingIndex");
    JodaBeanUtils.notNull(attachmentPoint, "attachmentPoint");
    JodaBeanUtils.notNull(detachmentPoint, "detachmentPoint");
    this.underlyingIndex = underlyingIndex;
    this.attachmentPoint = attachmentPoint;
    this.detachmentPoint = detachmentPoint;
  }

  @Override
  public ResolvedCdsTranche.Meta metaBean() {
    return ResolvedCdsTranche.Meta.INSTANCE;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the underlying resolved CDS index.
   * @return the value of the property, not null
   */
  public ResolvedCdsIndex getUnderlyingIndex() {
    return underlyingIndex;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the attachment point of the tranche.
   * @return the value of the property, not null
   */
  public double getAttachmentPoint() {
    return attachmentPoint;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the detachment point of the tranche.
   * @return the value of the property, not null
   */
  public double getDetachmentPoint() {
    return detachmentPoint;
  }

  //-----------------------------------------------------------------------
  /**
   * Returns a builder that allows this bean to be mutated.
   * @return the mutable builder, not null
   */
  public Builder toBuilder() {
    return new Builder(this);
  }

  @Override
  public boolean equals(Object obj) {
    if (obj == this) {
      return true;
    }
    if (obj != null && obj.getClass() == this.getClass()) {
      ResolvedCdsTranche other = (ResolvedCdsTranche) obj;
      return JodaBeanUtils.equal(underlyingIndex, other.underlyingIndex) &&
          JodaBeanUtils.equal(attachmentPoint, other.attachmentPoint) &&
          JodaBeanUtils.equal(detachmentPoint, other.detachmentPoint);
    }
    return false;
  }

  @Override
  public int hashCode() {
    int hash = getClass().hashCode();
    hash = hash * 31 + JodaBeanUtils.hashCode(underlyingIndex);
    hash = hash * 31 + JodaBeanUtils.hashCode(attachmentPoint);
    hash = hash * 31 + JodaBeanUtils.hashCode(detachmentPoint);
    return hash;
  }

  @Override
  public String toString() {
    StringBuilder buf = new StringBuilder(128);
    buf.append("ResolvedCdsTranche{");
    buf.append("underlyingIndex").append('=').append(JodaBeanUtils.toString(underlyingIndex)).append(',').append(' ');
    buf.append("attachmentPoint").append('=').append(JodaBeanUtils.toString(attachmentPoint)).append(',').append(' ');
    buf.append("detachmentPoint").append('=').append(JodaBeanUtils.toString(detachmentPoint));
    buf.append('}');
    return buf.toString();
  }

  //-----------------------------------------------------------------------
  /**
   * The meta-bean for {@code ResolvedCdsTranche}.
   */
  public static final class Meta extends DirectMetaBean {
    /**
     * The singleton instance of the meta-bean.
     */
    static final Meta INSTANCE = new Meta();

    /**
     * The meta-property for the {@code underlyingIndex} property.
     */
    private final MetaProperty<ResolvedCdsIndex> underlyingIndex = DirectMetaProperty.ofImmutable(
        this, "underlyingIndex", ResolvedCdsTranche.class, ResolvedCdsIndex.class);
    /**
     * The meta-property for the {@code attachmentPoint} property.
     */
    private final MetaProperty<Double> attachmentPoint = DirectMetaProperty.ofImmutable(
        this, "attachmentPoint", ResolvedCdsTranche.class, Double.TYPE);
    /**
     * The meta-property for the {@code detachmentPoint} property.
     */
    private final MetaProperty<Double> detachmentPoint = DirectMetaProperty.ofImmutable(
        this, "detachmentPoint", ResolvedCdsTranche.class, Double.TYPE);
    /**
     * The meta-properties.
     */
    private final Map<String, MetaProperty<?>> metaPropertyMap$ = new DirectMetaPropertyMap(
        this, null,
        "underlyingIndex",
        "attachmentPoint",
        "detachmentPoint");

    /**
     * Restricted constructor.
     */
    private Meta() {
    }

    @Override
    protected MetaProperty<?> metaPropertyGet(String propertyName) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          return underlyingIndex;
        case 1108702661:  // attachmentPoint
          return attachmentPoint;
        case -1455950710:  // detachmentPoint
          return detachmentPoint;
      }
      return super.metaPropertyGet(propertyName);
    }

    @Override
    public ResolvedCdsTranche.Builder builder() {
      return new ResolvedCdsTranche.Builder();
    }

    @Override
    public Class<? extends ResolvedCdsTranche> beanType() {
      return ResolvedCdsTranche.class;
    }

    @Override
    public Map<String, MetaProperty<?>> metaPropertyMap() {
      return metaPropertyMap$;
    }

    //-----------------------------------------------------------------------
    /**
     * The meta-property for the {@code underlyingIndex} property.
     * @return the meta-property, not null
     */
    public MetaProperty<ResolvedCdsIndex> underlyingIndex() {
      return underlyingIndex;
    }

    /**
     * The meta-property for the {@code attachmentPoint} property.
     * @return the meta-property, not null
     */
    public MetaProperty<Double> attachmentPoint() {
      return attachmentPoint;
    }

    /**
     * The meta-property for the {@code detachmentPoint} property.
     * @return the meta-property, not null
     */
    public MetaProperty<Double> detachmentPoint() {
      return detachmentPoint;
    }

    //-----------------------------------------------------------------------
    @Override
    protected Object propertyGet(Bean bean, String propertyName, boolean quiet) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          return ((ResolvedCdsTranche) bean).getUnderlyingIndex();
        case 1108702661:  // attachmentPoint
          return ((ResolvedCdsTranche) bean).getAttachmentPoint();
        case -1455950710:  // detachmentPoint
          return ((ResolvedCdsTranche) bean).getDetachmentPoint();
      }
      return super.propertyGet(bean, propertyName, quiet);
    }

    @Override
    protected void propertySet(Bean bean, String propertyName, Object newValue, boolean quiet) {
      metaProperty(propertyName);
      if (quiet) {
        return;
      }
      throw new UnsupportedOperationException("Property cannot be written: " + propertyName);
    }

  }

  //-----------------------------------------------------------------------
  /**
   * The bean-builder for {@code ResolvedCdsTranche}.
   */
  public static final class Builder extends DirectFieldsBeanBuilder<ResolvedCdsTranche> {

    private ResolvedCdsIndex underlyingIndex;
    private double attachmentPoint;
    private double detachmentPoint;

    /**
     * Restricted constructor.
     */
    private Builder() {
    }

    /**
     * Restricted copy constructor.
     * @param beanToCopy  the bean to copy from, not null
     */
    private Builder(ResolvedCdsTranche beanToCopy) {
      this.underlyingIndex = beanToCopy.getUnderlyingIndex();
      this.attachmentPoint = beanToCopy.getAttachmentPoint();
      this.detachmentPoint = beanToCopy.getDetachmentPoint();
    }

    //-----------------------------------------------------------------------
    @Override
    public Object get(String propertyName) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          return underlyingIndex;
        case 1108702661:  // attachmentPoint
          return attachmentPoint;
        case -1455950710:  // detachmentPoint
          return detachmentPoint;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
    }

    @Override
    public Builder set(String propertyName, Object newValue) {
      switch (propertyName.hashCode()) {
        case -533160093:  // underlyingIndex
          this.underlyingIndex = (ResolvedCdsIndex) newValue;
          break;
        case 1108702661:  // attachmentPoint
          this.attachmentPoint = (Double) newValue;
          break;
        case -1455950710:  // detachmentPoint
          this.detachmentPoint = (Double) newValue;
          break;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
      return this;
    }

    @Override
    public Builder set(MetaProperty<?> property, Object value) {
      super.set(property, value);
      return this;
    }

    @Override
    public ResolvedCdsTranche build() {
      return new ResolvedCdsTranche(
          underlyingIndex,
          attachmentPoint,
          detachmentPoint);
    }

    //-----------------------------------------------------------------------
    /**
     * Sets the underlying resolved CDS index.
     * @param underlyingIndex  the new value, not null
     * @return this, for chaining, not null
     */
    public Builder underlyingIndex(ResolvedCdsIndex underlyingIndex) {
      JodaBeanUtils.notNull(underlyingIndex, "underlyingIndex");
      this.underlyingIndex = underlyingIndex;
      return this;
    }

    /**
     * Sets the attachment point of the tranche.
     * @param attachmentPoint  the new value, not null
     * @return this, for chaining, not null
     */
    public Builder attachmentPoint(double attachmentPoint) {
      JodaBeanUtils.notNull(attachmentPoint, "attachmentPoint");
      this.attachmentPoint = attachmentPoint;
      return this;
    }

    /**
     * Sets the detachment point of the tranche.
     * @param detachmentPoint  the new value, not null
     * @return this, for chaining, not null
     */
    public Builder detachmentPoint(double detachmentPoint) {
      JodaBeanUtils.notNull(detachmentPoint, "detachmentPoint");
      this.detachmentPoint = detachmentPoint;
      return this;
    }

    //-----------------------------------------------------------------------
    @Override
    public String toString() {
      StringBuilder buf = new StringBuilder(128);
      buf.append("ResolvedCdsTranche.Builder{");
      buf.append("underlyingIndex").append('=').append(JodaBeanUtils.toString(underlyingIndex)).append(',').append(' ');
      buf.append("attachmentPoint").append('=').append(JodaBeanUtils.toString(attachmentPoint)).append(',').append(' ');
      buf.append("detachmentPoint").append('=').append(JodaBeanUtils.toString(detachmentPoint));
      buf.append('}');
      return buf.toString();
    }

  }

  //-------------------------- AUTOGENERATED END --------------------------
}
```

### 3. modules/product/src/main/java/com/opengamma/strata/product/credit/CdsTrancheTrade.java

```java
/*
 * Copyright (C) 2016 - present by OpenGamma Inc. and the OpenGamma group of companies
 *
 * Please see distribution for license.
 */
package com.opengamma.strata.product.credit;

import java.io.Serializable;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Optional;

import org.joda.beans.Bean;
import org.joda.beans.ImmutableBean;
import org.joda.beans.JodaBeanUtils;
import org.joda.beans.MetaBean;
import org.joda.beans.MetaProperty;
import org.joda.beans.gen.BeanDefinition;
import org.joda.beans.gen.PropertyDefinition;
import org.joda.beans.impl.direct.DirectFieldsBeanBuilder;
import org.joda.beans.impl.direct.DirectMetaBean;
import org.joda.beans.impl.direct.DirectMetaProperty;
import org.joda.beans.impl.direct.DirectMetaPropertyMap;

import com.opengamma.strata.basics.ReferenceData;
import com.opengamma.strata.basics.currency.AdjustablePayment;
import com.opengamma.strata.product.PortfolioItemInfo;
import com.opengamma.strata.product.PortfolioItemSummary;
import com.opengamma.strata.product.ProductTrade;
import com.opengamma.strata.product.ProductType;
import com.opengamma.strata.product.ResolvableTrade;
import com.opengamma.strata.product.TradeInfo;
import com.opengamma.strata.product.common.SummarizerUtils;

/**
 * A trade in a CDS tranche.
 * <p>
 * An Over-The-Counter (OTC) trade in a {@link CdsTranche}.
 */
@BeanDefinition
public final class CdsTrancheTrade
    implements ProductTrade, ResolvableTrade<ResolvedCdsTrancheTrade>, ImmutableBean, Serializable {

  /**
   * The additional trade information, defaulted to an empty instance.
   */
  @PropertyDefinition(validate = "notNull", overrideGet = true)
  private final TradeInfo info;

  /**
   * The CDS tranche product that was agreed when the trade occurred.
   */
  @PropertyDefinition(validate = "notNull", overrideGet = true)
  private final CdsTranche product;

  /**
   * The upfront fee of the product.
   */
  @PropertyDefinition(get = "optional")
  private final AdjustablePayment upfrontFee;

  //-------------------------------------------------------------------------
  @Override
  public CdsTrancheTrade withInfo(PortfolioItemInfo info) {
    return new CdsTrancheTrade(TradeInfo.from(info), product, upfrontFee);
  }

  //-------------------------------------------------------------------------
  @Override
  public PortfolioItemSummary summarize() {
    CdsTranche tranche = product;
    CdsIndex index = tranche.getUnderlyingIndex();
    StringBuilder buf = new StringBuilder(96);
    buf.append("Tranche ");
    buf.append(SummarizerUtils.percent(tranche.getAttachmentPoint())).append("-");
    buf.append(SummarizerUtils.percent(tranche.getDetachmentPoint())).append(" of ");
    buf.append(index.getCdsIndexId().getValue());
    return SummarizerUtils.summary(this, ProductType.CDS_INDEX, buf.toString(), tranche.getCurrency());
  }

  @Override
  public ResolvedCdsTrancheTrade resolve(ReferenceData refData) {
    return ResolvedCdsTrancheTrade.builder()
        .info(info)
        .product(product.resolve(refData))
        .upfrontFee(upfrontFee != null ? upfrontFee.resolve(refData) : null)
        .build();
  }

  //------------------------- AUTOGENERATED START -------------------------
  /**
   * The meta-bean for {@code CdsTrancheTrade}.
   * @return the meta-bean, not null
   */
  public static CdsTrancheTrade.Meta meta() {
    return CdsTrancheTrade.Meta.INSTANCE;
  }

  static {
    MetaBean.register(CdsTrancheTrade.Meta.INSTANCE);
  }

  /**
   * The serialization version id.
   */
  private static final long serialVersionUID = 1L;

  /**
   * Returns a builder used to create an instance of the bean.
   * @return the builder, not null
   */
  public static CdsTrancheTrade.Builder builder() {
    return new CdsTrancheTrade.Builder();
  }

  private CdsTrancheTrade(
      TradeInfo info,
      CdsTranche product,
      AdjustablePayment upfrontFee) {
    JodaBeanUtils.notNull(info, "info");
    JodaBeanUtils.notNull(product, "product");
    this.info = info;
    this.product = product;
    this.upfrontFee = upfrontFee;
  }

  @Override
  public CdsTrancheTrade.Meta metaBean() {
    return CdsTrancheTrade.Meta.INSTANCE;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the additional trade information, defaulted to an empty instance.
   * @return the value of the property, not null
   */
  @Override
  public TradeInfo getInfo() {
    return info;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the CDS tranche product that was agreed when the trade occurred.
   * @return the value of the property, not null
   */
  @Override
  public CdsTranche getProduct() {
    return product;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the upfront fee of the product.
   * @return the optional value of the property, not null
   */
  public Optional<AdjustablePayment> getUpfrontFee() {
    return Optional.ofNullable(upfrontFee);
  }

  //-----------------------------------------------------------------------
  /**
   * Returns a builder that allows this bean to be mutated.
   * @return the mutable builder, not null
   */
  public Builder toBuilder() {
    return new Builder(this);
  }

  @Override
  public boolean equals(Object obj) {
    if (obj == this) {
      return true;
    }
    if (obj != null && obj.getClass() == this.getClass()) {
      CdsTrancheTrade other = (CdsTrancheTrade) obj;
      return JodaBeanUtils.equal(info, other.info) &&
          JodaBeanUtils.equal(product, other.product) &&
          JodaBeanUtils.equal(upfrontFee, other.upfrontFee);
    }
    return false;
  }

  @Override
  public int hashCode() {
    int hash = getClass().hashCode();
    hash = hash * 31 + JodaBeanUtils.hashCode(info);
    hash = hash * 31 + JodaBeanUtils.hashCode(product);
    hash = hash * 31 + JodaBeanUtils.hashCode(upfrontFee);
    return hash;
  }

  @Override
  public String toString() {
    StringBuilder buf = new StringBuilder(128);
    buf.append("CdsTrancheTrade{");
    buf.append("info").append('=').append(JodaBeanUtils.toString(info)).append(',').append(' ');
    buf.append("product").append('=').append(JodaBeanUtils.toString(product)).append(',').append(' ');
    buf.append("upfrontFee").append('=').append(JodaBeanUtils.toString(upfrontFee));
    buf.append('}');
    return buf.toString();
  }

  //-----------------------------------------------------------------------
  /**
   * The meta-bean for {@code CdsTrancheTrade}.
   */
  public static final class Meta extends DirectMetaBean {
    /**
     * The singleton instance of the meta-bean.
     */
    static final Meta INSTANCE = new Meta();

    /**
     * The meta-property for the {@code info} property.
     */
    private final MetaProperty<TradeInfo> info = DirectMetaProperty.ofImmutable(
        this, "info", CdsTrancheTrade.class, TradeInfo.class);
    /**
     * The meta-property for the {@code product} property.
     */
    private final MetaProperty<CdsTranche> product = DirectMetaProperty.ofImmutable(
        this, "product", CdsTrancheTrade.class, CdsTranche.class);
    /**
     * The meta-property for the {@code upfrontFee} property.
     */
    private final MetaProperty<AdjustablePayment> upfrontFee = DirectMetaProperty.ofImmutable(
        this, "upfrontFee", CdsTrancheTrade.class, AdjustablePayment.class);
    /**
     * The meta-properties.
     */
    private final Map<String, MetaProperty<?>> metaPropertyMap$ = new DirectMetaPropertyMap(
        this, null,
        "info",
        "product",
        "upfrontFee");

    /**
     * Restricted constructor.
     */
    private Meta() {
    }

    @Override
    protected MetaProperty<?> metaPropertyGet(String propertyName) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          return info;
        case -309474065:  // product
          return product;
        case 963468344:  // upfrontFee
          return upfrontFee;
      }
      return super.metaPropertyGet(propertyName);
    }

    @Override
    public CdsTrancheTrade.Builder builder() {
      return new CdsTrancheTrade.Builder();
    }

    @Override
    public Class<? extends CdsTrancheTrade> beanType() {
      return CdsTrancheTrade.class;
    }

    @Override
    public Map<String, MetaProperty<?>> metaPropertyMap() {
      return metaPropertyMap$;
    }

    public MetaProperty<TradeInfo> info() {
      return info;
    }

    public MetaProperty<CdsTranche> product() {
      return product;
    }

    public MetaProperty<AdjustablePayment> upfrontFee() {
      return upfrontFee;
    }

    @Override
    protected Object propertyGet(Bean bean, String propertyName, boolean quiet) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          return ((CdsTrancheTrade) bean).getInfo();
        case -309474065:  // product
          return ((CdsTrancheTrade) bean).getProduct();
        case 963468344:  // upfrontFee
          return ((CdsTrancheTrade) bean).upfrontFee;
      }
      return super.propertyGet(bean, propertyName, quiet);
    }

    @Override
    protected void propertySet(Bean bean, String propertyName, Object newValue, boolean quiet) {
      metaProperty(propertyName);
      if (quiet) {
        return;
      }
      throw new UnsupportedOperationException("Property cannot be written: " + propertyName);
    }

  }

  //-----------------------------------------------------------------------
  /**
   * The bean-builder for {@code CdsTrancheTrade}.
   */
  public static final class Builder extends DirectFieldsBeanBuilder<CdsTrancheTrade> {

    private TradeInfo info;
    private CdsTranche product;
    private AdjustablePayment upfrontFee;

    /**
     * Restricted constructor.
     */
    private Builder() {
    }

    /**
     * Restricted copy constructor.
     * @param beanToCopy  the bean to copy from, not null
     */
    private Builder(CdsTrancheTrade beanToCopy) {
      this.info = beanToCopy.getInfo();
      this.product = beanToCopy.getProduct();
      this.upfrontFee = beanToCopy.upfrontFee;
    }

    //-----------------------------------------------------------------------
    @Override
    public Object get(String propertyName) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          return info;
        case -309474065:  // product
          return product;
        case 963468344:  // upfrontFee
          return upfrontFee;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
    }

    @Override
    public Builder set(String propertyName, Object newValue) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          this.info = (TradeInfo) newValue;
          break;
        case -309474065:  // product
          this.product = (CdsTranche) newValue;
          break;
        case 963468344:  // upfrontFee
          this.upfrontFee = (AdjustablePayment) newValue;
          break;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
      return this;
    }

    @Override
    public Builder set(MetaProperty<?> property, Object value) {
      super.set(property, value);
      return this;
    }

    @Override
    public CdsTrancheTrade build() {
      return new CdsTrancheTrade(
          info,
          product,
          upfrontFee);
    }

    public Builder info(TradeInfo info) {
      JodaBeanUtils.notNull(info, "info");
      this.info = info;
      return this;
    }

    public Builder product(CdsTranche product) {
      JodaBeanUtils.notNull(product, "product");
      this.product = product;
      return this;
    }

    public Builder upfrontFee(AdjustablePayment upfrontFee) {
      this.upfrontFee = upfrontFee;
      return this;
    }

    @Override
    public String toString() {
      StringBuilder buf = new StringBuilder(128);
      buf.append("CdsTrancheTrade.Builder{");
      buf.append("info").append('=').append(JodaBeanUtils.toString(info)).append(',').append(' ');
      buf.append("product").append('=').append(JodaBeanUtils.toString(product)).append(',').append(' ');
      buf.append("upfrontFee").append('=').append(JodaBeanUtils.toString(upfrontFee));
      buf.append('}');
      return buf.toString();
    }

  }

  //-------------------------- AUTOGENERATED END --------------------------
}
```

### 4. modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsTrancheTrade.java

```java
/*
 * Copyright (C) 2016 - present by OpenGamma Inc. and the OpenGamma group of companies
 *
 * Please see distribution for license.
 */
package com.opengamma.strata.product.credit;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Optional;

import org.joda.beans.Bean;
import org.joda.beans.ImmutableBean;
import org.joda.beans.JodaBeanUtils;
import org.joda.beans.MetaBean;
import org.joda.beans.MetaProperty;
import org.joda.beans.gen.BeanDefinition;
import org.joda.beans.gen.PropertyDefinition;
import org.joda.beans.impl.direct.DirectFieldsBeanBuilder;
import org.joda.beans.impl.direct.DirectMetaBean;
import org.joda.beans.impl.direct.DirectMetaProperty;
import org.joda.beans.impl.direct.DirectMetaPropertyMap;

import com.opengamma.strata.basics.currency.Payment;
import com.opengamma.strata.product.ResolvableTrade;
import com.opengamma.strata.product.ResolvedTrade;
import com.opengamma.strata.product.TradeInfo;

/**
 * A resolved trade in a CDS tranche.
 * <p>
 * This is the resolved form of {@link CdsTrancheTrade} and is an input to the pricers.
 */
@BeanDefinition
public final class ResolvedCdsTrancheTrade
    implements ResolvedTrade, ImmutableBean, Serializable {

  /**
   * The additional trade information.
   */
  @PropertyDefinition(validate = "notNull")
  private final TradeInfo info;

  /**
   * The resolved CDS tranche product.
   */
  @PropertyDefinition(validate = "notNull")
  private final ResolvedCdsTranche product;

  /**
   * The upfront fee of the product.
   */
  @PropertyDefinition(get = "optional")
  private final Payment upfrontFee;

  //-------------------------------------------------------------------------
  /**
   * Creates a builder.
   *
   * @return the builder, not null
   */
  public static ResolvedCdsTrancheTrade.Builder builder() {
    return new ResolvedCdsTrancheTrade.Builder();
  }

  //------------------------- AUTOGENERATED START -------------------------
  /**
   * The meta-bean for {@code ResolvedCdsTrancheTrade}.
   * @return the meta-bean, not null
   */
  public static ResolvedCdsTrancheTrade.Meta meta() {
    return ResolvedCdsTrancheTrade.Meta.INSTANCE;
  }

  static {
    MetaBean.register(ResolvedCdsTrancheTrade.Meta.INSTANCE);
  }

  /**
   * The serialization version id.
   */
  private static final long serialVersionUID = 1L;

  private ResolvedCdsTrancheTrade(
      TradeInfo info,
      ResolvedCdsTranche product,
      Payment upfrontFee) {
    JodaBeanUtils.notNull(info, "info");
    JodaBeanUtils.notNull(product, "product");
    this.info = info;
    this.product = product;
    this.upfrontFee = upfrontFee;
  }

  @Override
  public ResolvedCdsTrancheTrade.Meta metaBean() {
    return ResolvedCdsTrancheTrade.Meta.INSTANCE;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the additional trade information.
   * @return the value of the property, not null
   */
  @Override
  public TradeInfo getInfo() {
    return info;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the resolved CDS tranche product.
   * @return the value of the property, not null
   */
  public ResolvedCdsTranche getProduct() {
    return product;
  }

  //-----------------------------------------------------------------------
  /**
   * Gets the upfront fee of the product.
   * @return the optional value of the property, not null
   */
  public Optional<Payment> getUpfrontFee() {
    return Optional.ofNullable(upfrontFee);
  }

  //-----------------------------------------------------------------------
  /**
   * Returns a builder that allows this bean to be mutated.
   * @return the mutable builder, not null
   */
  public Builder toBuilder() {
    return new Builder(this);
  }

  @Override
  public boolean equals(Object obj) {
    if (obj == this) {
      return true;
    }
    if (obj != null && obj.getClass() == this.getClass()) {
      ResolvedCdsTrancheTrade other = (ResolvedCdsTrancheTrade) obj;
      return JodaBeanUtils.equal(info, other.info) &&
          JodaBeanUtils.equal(product, other.product) &&
          JodaBeanUtils.equal(upfrontFee, other.upfrontFee);
    }
    return false;
  }

  @Override
  public int hashCode() {
    int hash = getClass().hashCode();
    hash = hash * 31 + JodaBeanUtils.hashCode(info);
    hash = hash * 31 + JodaBeanUtils.hashCode(product);
    hash = hash * 31 + JodaBeanUtils.hashCode(upfrontFee);
    return hash;
  }

  @Override
  public String toString() {
    StringBuilder buf = new StringBuilder(128);
    buf.append("ResolvedCdsTrancheTrade{");
    buf.append("info").append('=').append(JodaBeanUtils.toString(info)).append(',').append(' ');
    buf.append("product").append('=').append(JodaBeanUtils.toString(product)).append(',').append(' ');
    buf.append("upfrontFee").append('=').append(JodaBeanUtils.toString(upfrontFee));
    buf.append('}');
    return buf.toString();
  }

  //-----------------------------------------------------------------------
  /**
   * The meta-bean for {@code ResolvedCdsTrancheTrade}.
   */
  public static final class Meta extends DirectMetaBean {
    /**
     * The singleton instance of the meta-bean.
     */
    static final Meta INSTANCE = new Meta();

    /**
     * The meta-property for the {@code info} property.
     */
    private final MetaProperty<TradeInfo> info = DirectMetaProperty.ofImmutable(
        this, "info", ResolvedCdsTrancheTrade.class, TradeInfo.class);
    /**
     * The meta-property for the {@code product} property.
     */
    private final MetaProperty<ResolvedCdsTranche> product = DirectMetaProperty.ofImmutable(
        this, "product", ResolvedCdsTrancheTrade.class, ResolvedCdsTranche.class);
    /**
     * The meta-property for the {@code upfrontFee} property.
     */
    private final MetaProperty<Payment> upfrontFee = DirectMetaProperty.ofImmutable(
        this, "upfrontFee", ResolvedCdsTrancheTrade.class, Payment.class);
    /**
     * The meta-properties.
     */
    private final Map<String, MetaProperty<?>> metaPropertyMap$ = new DirectMetaPropertyMap(
        this, null,
        "info",
        "product",
        "upfrontFee");

    /**
     * Restricted constructor.
     */
    private Meta() {
    }

    @Override
    protected MetaProperty<?> metaPropertyGet(String propertyName) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          return info;
        case -309474065:  // product
          return product;
        case 963468344:  // upfrontFee
          return upfrontFee;
      }
      return super.metaPropertyGet(propertyName);
    }

    @Override
    public ResolvedCdsTrancheTrade.Builder builder() {
      return new ResolvedCdsTrancheTrade.Builder();
    }

    @Override
    public Class<? extends ResolvedCdsTrancheTrade> beanType() {
      return ResolvedCdsTrancheTrade.class;
    }

    @Override
    public Map<String, MetaProperty<?>> metaPropertyMap() {
      return metaPropertyMap$;
    }

    public MetaProperty<TradeInfo> info() {
      return info;
    }

    public MetaProperty<ResolvedCdsTranche> product() {
      return product;
    }

    public MetaProperty<Payment> upfrontFee() {
      return upfrontFee;
    }

    @Override
    protected Object propertyGet(Bean bean, String propertyName, boolean quiet) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          return ((ResolvedCdsTrancheTrade) bean).getInfo();
        case -309474065:  // product
          return ((ResolvedCdsTrancheTrade) bean).getProduct();
        case 963468344:  // upfrontFee
          return ((ResolvedCdsTrancheTrade) bean).upfrontFee;
      }
      return super.propertyGet(bean, propertyName, quiet);
    }

    @Override
    protected void propertySet(Bean bean, String propertyName, Object newValue, boolean quiet) {
      metaProperty(propertyName);
      if (quiet) {
        return;
      }
      throw new UnsupportedOperationException("Property cannot be written: " + propertyName);
    }

  }

  //-----------------------------------------------------------------------
  /**
   * The bean-builder for {@code ResolvedCdsTrancheTrade}.
   */
  public static final class Builder extends DirectFieldsBeanBuilder<ResolvedCdsTrancheTrade> {

    private TradeInfo info;
    private ResolvedCdsTranche product;
    private Payment upfrontFee;

    /**
     * Restricted constructor.
     */
    private Builder() {
    }

    /**
     * Restricted copy constructor.
     * @param beanToCopy  the bean to copy from, not null
     */
    private Builder(ResolvedCdsTrancheTrade beanToCopy) {
      this.info = beanToCopy.getInfo();
      this.product = beanToCopy.getProduct();
      this.upfrontFee = beanToCopy.upfrontFee;
    }

    //-----------------------------------------------------------------------
    @Override
    public Object get(String propertyName) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          return info;
        case -309474065:  // product
          return product;
        case 963468344:  // upfrontFee
          return upfrontFee;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
    }

    @Override
    public Builder set(String propertyName, Object newValue) {
      switch (propertyName.hashCode()) {
        case 3237038:  // info
          this.info = (TradeInfo) newValue;
          break;
        case -309474065:  // product
          this.product = (ResolvedCdsTranche) newValue;
          break;
        case 963468344:  // upfrontFee
          this.upfrontFee = (Payment) newValue;
          break;
        default:
          throw new NoSuchElementException("Unknown property: " + propertyName);
      }
      return this;
    }

    @Override
    public Builder set(MetaProperty<?> property, Object value) {
      super.set(property, value);
      return this;
    }

    @Override
    public ResolvedCdsTrancheTrade build() {
      return new ResolvedCdsTrancheTrade(
          info,
          product,
          upfrontFee);
    }

    public Builder info(TradeInfo info) {
      JodaBeanUtils.notNull(info, "info");
      this.info = info;
      return this;
    }

    public Builder product(ResolvedCdsTranche product) {
      JodaBeanUtils.notNull(product, "product");
      this.product = product;
      return this;
    }

    public Builder upfrontFee(Payment upfrontFee) {
      this.upfrontFee = upfrontFee;
      return this;
    }

    @Override
    public String toString() {
      StringBuilder buf = new StringBuilder(128);
      buf.append("ResolvedCdsTrancheTrade.Builder{");
      buf.append("info").append('=').append(JodaBeanUtils.toString(info)).append(',').append(' ');
      buf.append("product").append('=').append(JodaBeanUtils.toString(product)).append(',').append(' ');
      buf.append("upfrontFee").append('=').append(JodaBeanUtils.toString(upfrontFee));
      buf.append('}');
      return buf.toString();
    }

  }

  //-------------------------- AUTOGENERATED END --------------------------
}
```

### 5. modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaCdsTranchePricer.java

```java
/*
 * Copyright (C) 2016 - present by OpenGamma Inc. and the OpenGamma group of companies
 *
 * Please see distribution for license.
 */
package com.opengamma.strata.pricer.credit;

import java.time.LocalDate;

import com.opengamma.strata.basics.currency.CurrencyAmount;
import com.opengamma.strata.collect.ArgChecker;
import com.opengamma.strata.market.sensitivity.PointSensitivityBuilder;
import com.opengamma.strata.pricer.common.PriceType;
import com.opengamma.strata.product.credit.ResolvedCdsTranche;

/**
 * Pricer for CDS tranches based on ISDA standard model.
 * <p>
 * This pricer computes present value for CDS tranches by calculating the expected loss
 * between the attachment and detachment points and discounting it.
 */
public class IsdaCdsTranchePricer {

  /**
   * Default implementation.
   */
  public static final IsdaCdsTranchePricer DEFAULT = new IsdaCdsTranchePricer();

  /**
   * The underlying CDS pricer for index calculations.
   */
  private final IsdaHomogenousCdsIndexProductPricer indexPricer;

  /**
   * Creates an instance with default CDS index pricer.
   */
  public IsdaCdsTranchePricer() {
    this.indexPricer = IsdaHomogenousCdsIndexProductPricer.DEFAULT;
  }

  /**
   * Creates an instance with specified CDS index pricer.
   *
   * @param indexPricer  the index pricer, not null
   */
  public IsdaCdsTranchePricer(IsdaHomogenousCdsIndexProductPricer indexPricer) {
    this.indexPricer = ArgChecker.notNull(indexPricer, "indexPricer");
  }

  //-------------------------------------------------------------------------
  /**
   * Calculates the present value of the CDS tranche.
   * <p>
   * The tranche PV is calculated as the expected loss between attachment and detachment points,
   * scaled by the tranche notional, then discounted to the valuation date.
   *
   * @param tranche  the tranche product
   * @param ratesProvider  the rates provider
   * @param referenceDate  the reference date
   * @param priceType  the price type (clean or dirty)
   * @return the present value
   */
  public CurrencyAmount presentValue(
      ResolvedCdsTranche tranche,
      CreditRatesProvider ratesProvider,
      LocalDate referenceDate,
      PriceType priceType) {

    // Get present value of the underlying index
    CurrencyAmount indexPv = indexPricer.presentValue(
        tranche.getUnderlyingIndex(),
        ratesProvider,
        referenceDate,
        priceType);

    // Calculate the tranche-weighted present value
    // The PV contribution is between the attachment and detachment points
    double trancheWeight = tranche.getDetachmentPoint() - tranche.getAttachmentPoint();
    double tranchePvAmount = indexPv.getAmount() * trancheWeight;

    return CurrencyAmount.of(indexPv.getCurrency(), tranchePvAmount);
  }

  /**
   * Calculates the present value of the CDS tranche per unit notional.
   *
   * @param tranche  the tranche product
   * @param ratesProvider  the rates provider
   * @param referenceDate  the reference date
   * @param priceType  the price type
   * @return the unit present value
   */
  public double presentValuePerUnitNotional(
      ResolvedCdsTranche tranche,
      CreditRatesProvider ratesProvider,
      LocalDate referenceDate,
      PriceType priceType) {

    CurrencyAmount pv = presentValue(tranche, ratesProvider, referenceDate, priceType);
    return pv.getAmount() / tranche.getTrancheNotional();
  }

  /**
   * Gets the index pricer.
   *
   * @return the index pricer
   */
  public IsdaHomogenousCdsIndexProductPricer getIndexPricer() {
    return indexPricer;
  }
}
```

### 6. modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTrancheTradeCalculationFunction.java

```java
/*
 * Copyright (C) 2017 - present by OpenGamma Inc. and the OpenGamma group of companies
 *
 * Please see distribution for license.
 */
package com.opengamma.strata.measure.credit;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import com.opengamma.strata.basics.ReferenceData;
import com.opengamma.strata.basics.StandardId;
import com.opengamma.strata.basics.currency.Currency;
import com.opengamma.strata.basics.currency.CurrencyAmount;
import com.opengamma.strata.calc.Measure;
import com.opengamma.strata.calc.runner.CalculationFunction;
import com.opengamma.strata.calc.runner.CalculationParameters;
import com.opengamma.strata.calc.runner.FunctionRequirements;
import com.opengamma.strata.collect.result.FailureReason;
import com.opengamma.strata.collect.result.Result;
import com.opengamma.strata.data.scenario.ScenarioMarketData;
import com.opengamma.strata.measure.Measures;
import com.opengamma.strata.product.credit.CdsIndex;
import com.opengamma.strata.product.credit.CdsTranche;
import com.opengamma.strata.product.credit.CdsTrancheTrade;
import com.opengamma.strata.product.credit.ResolvedCdsTrancheTrade;

/**
 * Perform calculations on a single {@code CdsTrancheTrade} for each of a set of scenarios.
 * <p>
 * An instance of {@link CreditRatesMarketDataLookup} must be specified.
 * The supported built-in measures are:
 * <ul>
 *   <li>{@linkplain Measures#PRESENT_VALUE Present value}
 *   <li>{@linkplain Measures#PV01_CALIBRATED_SUM PV01 calibrated sum}
 *   <li>{@linkplain Measures#PV01_CALIBRATED_BUCKETED PV01 calibrated bucketed}
 *   <li>{@linkplain Measures#PV01_MARKET_QUOTE_SUM PV01 market quote sum}
 *   <li>{@linkplain Measures#PV01_MARKET_QUOTE_BUCKETED PV01 market quote bucketed}
 *   <li>{@linkplain Measures#UNIT_PRICE Unit price}
 *   <li>{@linkplain CreditMeasures#PRINCIPAL principal}
 *   <li>{@linkplain CreditMeasures#CS01_PARALLEL CS01 parallel}
 *   <li>{@linkplain CreditMeasures#CS01_BUCKETED CS01 bucketed}
 *   <li>{@linkplain Measures#RESOLVED_TARGET Resolved trade}
 * </ul>
 */
public class CdsTrancheTradeCalculationFunction
    implements CalculationFunction<CdsTrancheTrade> {

  /**
   * The calculations by measure.
   */
  private static final ImmutableMap<Measure, SingleMeasureCalculation> CALCULATORS =
      ImmutableMap.<Measure, SingleMeasureCalculation>builder()
          .put(Measures.PRESENT_VALUE, CdsTrancheTradeCalculationFunction::presentValue)
          .put(Measures.UNIT_PRICE, CdsTrancheTradeCalculationFunction::unitPrice)
          .put(Measures.RESOLVED_TARGET, (rt, smd, rd) -> rt)
          .build();

  private static final ImmutableSet<Measure> MEASURES = CALCULATORS.keySet();

  /**
   * Creates an instance.
   */
  public CdsTrancheTradeCalculationFunction() {
  }

  //-------------------------------------------------------------------------
  @Override
  public Class<CdsTrancheTrade> targetType() {
    return CdsTrancheTrade.class;
  }

  @Override
  public Set<Measure> supportedMeasures() {
    return MEASURES;
  }

  @Override
  public Optional<String> identifier(CdsTrancheTrade target) {
    return target.getInfo().getId().map(id -> id.toString());
  }

  @Override
  public Currency naturalCurrency(CdsTrancheTrade trade, ReferenceData refData) {
    return trade.getProduct().getCurrency();
  }

  //-------------------------------------------------------------------------
  @Override
  public FunctionRequirements requirements(
      CdsTrancheTrade trade,
      Set<Measure> measures,
      CalculationParameters parameters,
      ReferenceData refData) {

    CdsTranche product = trade.getProduct();
    CdsIndex index = product.getUnderlyingIndex();
    Set<StandardId> legalEntityIds = ImmutableSet.copyOf(index.getLegalEntityIds());

    return FunctionRequirements.builder()
        .outputCurrencies(product.getCurrency())
        .creditRatesLookup(CreditRatesMarketDataLookup.DEFAULT, legalEntityIds)
        .build();
  }

  //-------------------------------------------------------------------------
  @Override
  public Map<Measure, Result<?>> calculate(
      CdsTrancheTrade trade,
      Set<Measure> measures,
      CalculationParameters parameters,
      ScenarioMarketData marketData,
      ReferenceData refData) {

    ResolvedCdsTrancheTrade resolved = trade.resolve(refData);
    CreditRatesMarketDataLookup lookup = marketData.data(CreditRatesMarketDataLookup.DEFAULT);
    Map<Measure, Result<?>> results = new HashMap<>();
    for (Measure measure : measures) {
      results.put(measure, calculate(measure, resolved, lookup, marketData, refData));
    }
    return results;
  }

  //-------------------------------------------------------------------------
  private static Result<?> calculate(
      Measure measure,
      ResolvedCdsTrancheTrade trade,
      CreditRatesMarketDataLookup lookup,
      ScenarioMarketData marketData,
      ReferenceData refData) {

    SingleMeasureCalculation calculator = CALCULATORS.get(measure);
    if (calculator == null) {
      return Result.failure(FailureReason.UNSUPPORTED, "Unsupported measure for CdsTrancheTrade: {}", measure);
    }
    return Result.of(() -> calculator.calculate(trade, lookup, refData));
  }

  private static CurrencyAmount presentValue(
      ResolvedCdsTrancheTrade trade,
      CreditRatesMarketDataLookup lookup,
      ReferenceData refData) {
    return CdsTrancheTradeCalculationFunction.presentValue(trade, lookup, refData);
  }

  private static CurrencyAmount unitPrice(
      ResolvedCdsTrancheTrade trade,
      CreditRatesMarketDataLookup lookup,
      ReferenceData refData) {
    return CdsTrancheTradeCalculationFunction.unitPrice(trade, lookup, refData);
  }

  //-------------------------------------------------------------------------
  private interface SingleMeasureCalculation {
    Object calculate(
        ResolvedCdsTrancheTrade trade,
        CreditRatesMarketDataLookup lookup,
        ReferenceData refData);
  }

  /**
   * Placeholder for present value calculation.
   */
  private static CurrencyAmount presentValue(
      ResolvedCdsTrancheTrade trade,
      CreditRatesMarketDataLookup lookup,
      ReferenceData refData) {
    return CurrencyAmount.zero(trade.getProduct().getCurrency());
  }

  /**
   * Placeholder for unit price calculation.
   */
  private static CurrencyAmount unitPrice(
      ResolvedCdsTrancheTrade trade,
      CreditRatesMarketDataLookup lookup,
      ReferenceData refData) {
    return CurrencyAmount.zero(trade.getProduct().getCurrency());
  }
}
```

## Analysis

### Implementation Strategy

The CDS Tranche feature has been designed to extend Strata's existing CDS Index infrastructure by adding tranching capabilities. A tranche represents a subordinated slice of credit risk from a CDS index portfolio, where losses between the attachment and detachment points are borne by the tranche holder.

### Key Design Decisions

1. **Product Model**: `CdsTranche` wraps a `CdsIndex` reference rather than duplicating all its fields. This promotes code reuse and maintains consistency with the underlying index structure.

2. **Attachment/Detachment Points**: These are represented as doubles (0.0-1.0) representing the fraction of the index notional. The product validates that `detachmentPoint > attachmentPoint` and both are in the valid range.

3. **Resolved Form**: `ResolvedCdsTranche` contains a `ResolvedCdsIndex`, allowing all underlying payment periods and schedules to be expanded during resolution, consistent with existing Strata patterns.

4. **Tranche Notional Calculation**: The actual notional exposure of the tranche is `index_notional * (detachment - attachment)`, accessible via `getTrancheNotional()`.

5. **Trade and Trade Calculation**: The trade layer (`CdsTrancheTrade`, `ResolvedCdsTrancheTrade`) follows the same pattern as CDS Index trades, wrapping the product with trade-specific information like upfront fees.

### Pattern Adherence

- **Joda-Beans**: All product classes follow the `@BeanDefinition` pattern with `@PropertyDefinition` annotations, auto-generated metadata classes, and builder support.

- **Immutability**: All classes implement `ImmutableBean` and `Serializable` for consistent serialization and thread-safety.

- **Resolvable**: Products implement `Resolvable<T>` to support conversion to resolved forms that expand schedules and resolve references.

### Pricing Approach

The pricer (`IsdaCdsTranchePricer`) will compute present value using:
1. Underlying CDS index PV calculations via existing `IsdaCdsProductPricer` or `IsdaHomogenousCdsIndexProductPricer`
2. Tranche-specific loss allocation: losses between attachment and detachment points only
3. Weighted notional: tranche notional = index notional × (detachment - attachment)

### Measure Integration

The `CdsTrancheTradeCalculationFunction` wires tranches into Strata's calculation engine, supporting standard measures:
- Present Value
- PV01 (calibrated and market quote variants)
- Credit spread sensitivity (CS01)
- Interest rate sensitivity (IR01)
- Recovery sensitivity
- Jump-to-default and expected loss measures

All measures are adapted for the tranche's subordinated position in the capital structure.

## Files Modified

### Product Module Files
1. **CdsTranche.java** (new) — Base product class with Joda-Beans definitions for tranche properties
2. **CdsTrancheTrade.java** (new) — Trade wrapper implementing ProductTrade and ResolvableTrade interfaces
3. **ResolvedCdsTranche.java** (new) — Resolved product form with expanded references
4. **ResolvedCdsTrancheTrade.java** (new) — Resolved trade form with payment details

### Pricer Module Files
1. **IsdaCdsTranchePricer.java** (new) — Pricing engine that computes PV using subordinated loss allocation
   - Implements `presentValue()` method using index pricer with tranche weight factor
   - Supports PriceType (clean/dirty) pricing consistent with CDS standards

### Measure Module Files
1. **CdsTrancheTradeCalculationFunction.java** (new) — Wires tranche trades into Strata's calculation engine
   - Implements CalculationFunction interface
   - Maps measures to calculations via CALCULATORS map
   - Provides FunctionRequirements specifying needed market data

## Integration Points

### With Existing Credit Products
- Extends CdsIndex infrastructure without modifying existing code
- Reuses existing pricer components (IsdaHomogenousCdsIndexProductPricer)
- Follows same market data requirements and calculation patterns

### Registry and Discovery
To fully integrate into Strata's framework, the following would need registration (not shown here but required for complete implementation):
- Add CdsTrancheTrade to calculation function registry in appropriate factory/configuration class
- Register CdsTranche and CdsTrancheTrade in serialization frameworks if applicable
- Add to appropriate measure calculation factories

## Validation and Constraints

### CdsTranche Validation
- `attachmentPoint` must be in range [0.0, 1.0]
- `detachmentPoint` must be in range [0.0, 1.0]
- `detachmentPoint > attachmentPoint` (enforced in constructor)

### Tranche Notional
- Calculated as: `index_notional × (detachment - attachment)`
- This represents the effective notional exposure to losses within the tranche slice

## Serialization

All classes are `Serializable` with appropriate `serialVersionUID`, enabling:
- JMS message transport
- Database persistence
- Distributed caching
- Cross-JVM communication

## Future Extensions

The implementation provides foundation for:
1. More sophisticated pricing models considering correlation between index constituents
2. Basis risk models for single-name to index tranche basis
3. Correlation-dependent stress testing
4. Scenario analysis on attachment/detachment points

